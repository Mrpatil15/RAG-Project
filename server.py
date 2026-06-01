import os
import glob
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(title="Mumbai Real Estate RAG Backend")

# Enable CORS for local testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request schema
class ChatRequest(BaseModel):
    question: str
    locality: str

# Local offline search helper (fallback when OpenAI key is missing)
def offline_search(query: str, locality_filter: str):
    files = glob.glob("./data/locality_briefs/*.md")
    query_words = [w.lower() for w in query.split() if len(w) > 2]
    
    results = []
    for f_path in files:
        file_name = os.path.basename(f_path)
        locality_stem = os.path.splitext(file_name)[0].lower()
        
        # Apply metadata locality filter if selected
        if locality_filter != "all" and locality_filter != locality_stem:
            continue
            
        with open(f_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        score = 0
        for word in query_words:
            score += content.lower().count(word) * 2
            if word in file_name.lower():
                score += 10
                
        if score > 0:
            paragraphs = content.split("\n\n")
            best_paragraph = ""
            best_p_score = -1
            for p in paragraphs:
                p_score = sum(p.lower().count(w) for w in query_words)
                if p_score > best_p_score:
                    best_p_score = p_score
                    best_paragraph = p
                    
            results.append((score, file_name, best_paragraph))
            
    results.sort(key=lambda x: x[0], reverse=True)
    return results

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    question = request.question
    locality = request.locality.lower()
    
    api_key = os.getenv("OPENAI_API_KEY")
    
    # Check if we should use actual RAG or fallback mock search
    if not api_key or api_key == "your_openai_api_key_here":
        # Fallback to local keyword search
        matches = offline_search(question, locality)
        if matches:
            top_score, file_name, text = matches[0]
            answer = (
                f"[OFFLINE FALLBACK MODE - No OpenAI Key Configured]\n\n"
                f"Based on the local source document **{file_name}**, here are the details:\n\n"
                f"{text.strip()}\n\n"
                f"*(To enable actual AI generation, please add your OPENAI_API_KEY in the `.env` file and restart).* "
            )
            return {
                "answer": answer,
                "sources": [file_name]
            }
        else:
            return {
                "answer": "[OFFLINE FALLBACK MODE] I couldn't find any documents matching your search terms. Please try asking about specific localities like Kanjurmarg, Bhandup, Mulund, Vikhroli, South Mumbai, Western Suburbs, Navi Mumbai, or Thane.",
                "sources": []
            }
            
    # If OpenAI Key is present, run RAG chain
    try:
        from langchain_openai import OpenAIEmbeddings, ChatOpenAI
        from langchain_chroma import Chroma
        from langchain.prompts import PromptTemplate
        from langchain.chains import RetrievalQA
        
        DB_DIR = "./chroma_db"
        if not os.path.exists(DB_DIR):
            raise Exception("Chroma DB directory not found. Please run python ingest.py.")
            
        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        vectorstore = Chroma(
            collection_name="mumbai_realestate",
            embedding_function=embeddings,
            persist_directory=DB_DIR
        )
        
        search_kwargs = {"k": 4}
        if locality != "all":
            search_kwargs["filter"] = {"locality": locality}
            
        retriever = vectorstore.as_retriever(search_kwargs=search_kwargs)
        
        PROMPT_TEMPLATE = """You are an expert real estate consultant specializing in Mumbai.
Use the following pieces of context to answer the user's question. 
If you don't know the answer or if the context does not contain enough information, say that you don't know—do not try to make up an answer.
Always cite the source document names when giving statistics, price ranges, or project names.

Context:
{context}

Question: {question}

Helpful Answer:"""

        prompt = PromptTemplate(
            template=PROMPT_TEMPLATE,
            input_variables=["context", "question"]
        )
        
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=retriever,
            chain_type_kwargs={"prompt": prompt},
            return_source_documents=True
        )
        
        response = chain.invoke(question)
        answer = response["result"]
        source_docs = response.get("source_documents", [])
        sources = list(set([doc.metadata.get("source", "Unknown") for doc in source_docs]))
        
        return {
            "answer": answer,
            "sources": sources
        }
        
    except Exception as e:
        error_msg = str(e).lower()
        warning_msg = "[OFFLINE MODE - RAG Pipeline Fallback]\n\n"
        if "insufficient_quota" in error_msg:
            warning_msg = (
                "⚠️ **[OFFLINE MODE - OpenAI Quota Exceeded]**\n"
                "Your OpenAI API Key is valid, but your OpenAI developer account has run out of credits or has no billing method configured.\n"
                "Temporarily using local keyword search to answer your question:\n\n"
            )
        elif "chroma db directory not found" in error_msg:
            warning_msg = (
                "⚠️ **[OFFLINE MODE - Vector DB Not Ready]**\n"
                "The Chroma database is not initialized. Using local keyword search to answer your question:\n\n"
            )
            
        matches = offline_search(question, locality)
        if matches:
            top_score, file_name, text = matches[0]
            return {
                "answer": f"{warning_msg}Based on the local source document **{file_name}**:\n\n{text.strip()}",
                "sources": [file_name]
            }
        else:
            return {
                "answer": f"{warning_msg}No matching documents were found offline. Please configure your OpenAI account billing or add credits to resolve this.",
                "sources": []
            }

# Mount frontend files statically at the root
# Note: Ensure frontend directory exists before mounting
os.makedirs("./frontend", exist_ok=True)
app.mount("/", StaticFiles(directory="./frontend", html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)
