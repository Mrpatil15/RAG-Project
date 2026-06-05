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
    zone: str
    locality: str

# MMR Localities mapping by Zone
ZONE_LOCALITIES = {
    "Central Eastern Suburbs": ["Kanjurmarg", "Bhandup", "Mulund", "Vikhroli", "Nahur"],
    "Central Mumbai": ["Dadar", "Kurla", "Ghatkopar", "Chembur", "Govandi", "Mankhurd", "Tilak Nagar"],
    "Western Mumbai": ["Andheri", "Borivali", "Kandivali", "Malad", "Goregaon", "Dahisar", "Mira Road", "Bhayandar"],
    "South & Harbour Mumbai": ["Bandra", "Worli", "Lower Parel", "Parel", "Wadala", "Sion", "Matunga", "Mahim"],
    "Thane District": ["Thane West", "Thane East", "Kalyan", "Dombivli", "Ulhasnagar", "Bhiwandi", "Ambernath", "Badlapur"],
    "Navi Mumbai": ["Vashi", "Kharghar", "Panvel", "Airoli", "Nerul", "Belapur", "Sanpada", "Ghansoli", "Kopar Khairane"]
}

# Global cached variables for vector stores
openai_vectorstore = None
local_vectorstore = None

# Initialize resources globally on startup to prevent slow response times
def preload_resources():
    global openai_vectorstore, local_vectorstore
    
    api_key = os.getenv("OPENAI_API_KEY")
    use_openai = api_key and api_key != "your_openai_api_key_here" and api_key != ""
    
    # 1. Preload OpenAI Vector Store (Online Mode)
    if use_openai:
        try:
            from langchain_openai import OpenAIEmbeddings
            from langchain_chroma import Chroma
            DB_DIR = "./chroma_db_openai"
            if not os.path.exists(DB_DIR):
                print("[INFO] OpenAI Vector database folder not found. Auto-generating it via ingest.py...")
                try:
                    import ingest
                    ingest.ingest_documents()
                except Exception as ingest_err:
                    print(f"[ERROR] Auto-ingestion failed: {ingest_err}")
            
            if os.path.exists(DB_DIR):
                embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
                openai_vectorstore = Chroma(
                    collection_name="mumbai_realestate",
                    embedding_function=embeddings,
                    persist_directory=DB_DIR
                )
                print("[INFO] Preloaded OpenAI Vector Store successfully.")
            else:
                print("[WARNING] OpenAI Vector database folder not found.")
        except Exception as e:
            print(f"[ERROR] Could not preload OpenAI Vector Store: {e}")
            
    # 2. Preload Local Vector Store (Offline Mode)
    try:
        from langchain_community.embeddings import HuggingFaceEmbeddings
        from langchain_chroma import Chroma
        DB_DIR = "./chroma_db_local"
        if not os.path.exists(DB_DIR):
            print("[INFO] Local Vector database folder not found. Auto-generating it via ingest.py...")
            try:
                import ingest
                ingest.ingest_documents()
            except Exception as ingest_err:
                print(f"[ERROR] Auto-ingestion failed: {ingest_err}")
                
        if os.path.exists(DB_DIR):
            embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
            local_vectorstore = Chroma(
                collection_name="mumbai_realestate",
                embedding_function=embeddings,
                persist_directory=DB_DIR
            )
            print("[INFO] Preloaded Local Vector Store successfully.")
        else:
            print("[WARNING] Local Vector database folder not found.")
    except Exception as e:
        print(f"[ERROR] Could not preload Local Vector Store: {e}")

# Preload resources
preload_resources()

# Local keyword offline search helper (fallback when both OpenAI and Ollama fail)
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
    zone = request.zone
    locality = request.locality.lower()
    
    api_key = os.getenv("OPENAI_API_KEY")
    use_openai = api_key and api_key != "your_openai_api_key_here" and api_key != ""

    # Setup prompt template
    PROMPT_TEMPLATE = """You are Hunter, an expert real estate consultant specializing in Mumbai.
Use the following pieces of context to answer the user's question. 
If you don't know the answer or if the context does not contain enough information, say that you don't know—do not try to make up an answer.
Always cite the source document names when giving statistics, price ranges, or project names.

Context:
{context}

Question: {question}

Helpful Answer:"""

    # --- MODE 1: CLOUD RAG (OpenAI) ---
    if use_openai and openai_vectorstore is not None:
        try:
            from langchain_openai import ChatOpenAI
            from langchain_core.prompts import PromptTemplate
            try:
                from langchain.chains import RetrievalQA
            except ImportError:
                from langchain_classic.chains import RetrievalQA
            
            search_kwargs = {"k": 4}
            if zone != "all" and zone in ZONE_LOCALITIES:
                if locality != "all":
                    search_kwargs["filter"] = {"locality": {"$eq": locality}}
                else:
                    search_kwargs["filter"] = {
                        "locality": {
                            "$in": [loc.lower() for loc in ZONE_LOCALITIES[zone]]
                        }
                    }
                
            retriever = openai_vectorstore.as_retriever(search_kwargs=search_kwargs)
            prompt = PromptTemplate(template=PROMPT_TEMPLATE, input_variables=["context", "question"])
            
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
            print(f"[OpenAI Mode Error] {e} - Falling back to local/offline search.")
            # Fall through to local RAG or keyword fallback

    # --- MODE 2: LOCAL RAG (HuggingFace + Ollama Llama3) ---
    if local_vectorstore is not None:
        try:
            from langchain_community.llms import Ollama
            from langchain_core.prompts import PromptTemplate
            try:
                from langchain.chains import RetrievalQA
            except ImportError:
                from langchain_classic.chains import RetrievalQA
            
            search_kwargs = {"k": 4}
            if zone != "all" and zone in ZONE_LOCALITIES:
                if locality != "all":
                    search_kwargs["filter"] = {"locality": {"$eq": locality}}
                else:
                    search_kwargs["filter"] = {
                        "locality": {
                            "$in": [loc.lower() for loc in ZONE_LOCALITIES[zone]]
                        }
                    }
                
            retriever = local_vectorstore.as_retriever(search_kwargs=search_kwargs)
            prompt = PromptTemplate(template=PROMPT_TEMPLATE, input_variables=["context", "question"])
            
            # Connect to local Ollama Llama-3 model
            llm = Ollama(model="llama3", temperature=0)
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
                "answer": f"🤖 **[Local Offline AI Mode]**\n\n{answer}",
                "sources": sources
            }
            
        except Exception as e:
            print(f"[Local RAG Error] {e} - Falling back to local keyword search.")
            
    # --- MODE 3: KEYWORD OFFLINE SEARCH (No libraries/Ollama needed) ---
    warning_msg = (
        "⚠️ **[Offline Mode - Keyword Fallback]**\n"
        "OpenAI API key was not found or has expired, and local Ollama (Llama-3) RAG is not running/initialized.\n"
        "Using direct document keyword matching to answer your query:\n\n"
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
            "answer": f"{warning_msg}No matching documents were found offline. Please start Ollama or run `python ingest.py` to index the local files for semantic search.",
            "sources": []
        }

# Mount frontend files statically at the root
os.makedirs("./frontend", exist_ok=True)
app.mount("/", StaticFiles(directory="./frontend", html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)
