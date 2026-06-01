import os
import streamlit as st
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_chroma import Chroma
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA

# Load env variables
load_dotenv()

# App Page Configurations
st.set_page_config(
    page_title="Mumbai Central Suburbs Real Estate RAG Chatbot",
    page_icon="🏢",
    layout="wide"
)

# Custom Premium Styling
st.markdown("""
    <style>
    .main {
        background-color: #0f172a;
        color: #f8fafc;
    }
    .stTextInput>div>div>input {
        background-color: #1e293b;
        color: #f8fafc;
        border: 1px solid #334155;
    }
    .stSelectbox>div>div {
        background-color: #1e293b;
        color: #f8fafc;
        border: 1px solid #334155;
    }
    .stButton>button {
        background-color: #3b82f6;
        color: white;
        border-radius: 6px;
        border: none;
        padding: 8px 16px;
    }
    .stButton>button:hover {
        background-color: #2563eb;
    }
    .stAlert {
        border-radius: 8px;
    }
    .chat-bubble {
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 10px;
    }
    .user-bubble {
        background-color: #1e293b;
        border-left: 4px solid #3b82f6;
    }
    .assistant-bubble {
        background-color: #0f172a;
        border-left: 4px solid #10b981;
    }
    </style>
""", unsafe_allowed_code=True)

st.title("🏢 Mumbai Real Estate Assistant")
st.markdown("### AI Agent for Kanjurmarg, Bhandup, Mulund, & Vikhroli Micro-markets")

# Sidebar configurations
with st.sidebar:
    st.header("Settings")
    
    # Check if API Key is available
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "your_openai_api_key_here":
        st.warning("⚠️ OpenAI API Key not found in .env file.")
        user_key = st.text_input("Enter OpenAI API Key:", type="password")
        if user_key:
            os.environ["OPENAI_API_KEY"] = user_key
            st.success("API Key applied locally!")
            api_key = user_key
    else:
        st.success("🔑 OpenAI API Key loaded from .env")
        
    st.subheader("Filter Settings")
    locality_filter = st.selectbox(
        "Focus Area (Metadata Filter):",
        ["All Localities", "Kanjurmarg", "Bhandup", "Mulund", "Vikhroli"]
    )
    
    st.info(
        "This chatbot uses Retrieval Augmented Generation (RAG). "
        "It retrieves local market knowledge from your briefs to ensure accurate, hallucination-free answers."
    )

# Vector store connection
DB_DIR = "./chroma_db"

@st.cache_resource
def get_vector_store():
    # If API key is not set, we cannot initialize embeddings
    if not os.getenv("OPENAI_API_KEY"):
        return None
    try:
        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        vectorstore = Chroma(
            collection_name="mumbai_realestate",
            embedding_function=embeddings,
            persist_directory=DB_DIR
        )
        return vectorstore
    except Exception as e:
        st.error(f"Error loading Vector Store: {e}")
        return None

# Check if vector DB is initialized
vectorstore = get_vector_store()

# System Prompt Template
PROMPT_TEMPLATE = """You are an expert real estate consultant specializing in Mumbai's central eastern suburbs: Kanjurmarg, Bhandup, Mulund, and Vikhroli.
Use the following pieces of context to answer the user's question. 
If you don't know the answer or if the context does not contain enough information, say that you don't know—do not try to make up an answer.
Always cite the source document names when giving statistics, price ranges, or project names.

Context:
{context}

Question: {question}

Helpful Answer:"""

# Chat session state initialization
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display conversation history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        if "sources" in msg and msg["sources"]:
            with st.expander("Show Sources Referenced"):
                for source in msg["sources"]:
                    st.caption(f"📄 Source File: {source}")

# Chat input
if user_query := st.chat_input("Ask about connectivity, projects, prices, or upcoming metro extensions..."):
    # 1. Show user message
    st.session_state.messages.append({"role": "user", "content": user_query})
    with st.chat_message("user"):
        st.write(user_query)

    # 2. Process query with RAG
    if not os.getenv("OPENAI_API_KEY"):
        with st.chat_message("assistant"):
            st.error("Please add your OpenAI API Key in the sidebar or `.env` file to query the model.")
    elif not vectorstore:
        with st.chat_message("assistant"):
            st.error("Vector Database not found. Please run `python ingest.py` first to index your documents.")
    else:
        with st.chat_message("assistant"):
            with st.spinner("Analyzing market data..."):
                try:
                    # Construct search arguments with optional metadata filter
                    search_kwargs = {"k": 4}
                    if locality_filter != "All Localities":
                        search_kwargs["filter"] = {"locality": locality_filter.lower()}

                    retriever = vectorstore.as_retriever(search_kwargs=search_kwargs)
                    
                    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
                    
                    prompt = PromptTemplate(
                        template=PROMPT_TEMPLATE,
                        input_variables=["context", "question"]
                    )
                    
                    chain = RetrievalQA.from_chain_type(
                        llm=llm,
                        chain_type="stuff",
                        retriever=retriever,
                        chain_type_kwargs={"prompt": prompt},
                        return_source_documents=True
                    )
                    
                    # Run query
                    response = chain.invoke(user_query)
                    answer = response["result"]
                    source_docs = response.get("source_documents", [])
                    
                    # Extract unique source names
                    sources = list(set([doc.metadata.get("source", "Unknown Source") for doc in source_docs]))
                    
                    # Display Answer
                    st.write(answer)
                    
                    if sources:
                        with st.expander("Show Sources Referenced"):
                            for source in sources:
                                st.caption(f"📄 Source File: {source}")
                                
                    # Save to session history
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": answer,
                        "sources": sources
                    })
                    
                except Exception as e:
                    st.error(f"An error occurred: {e}")
