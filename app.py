import os
import streamlit as st
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_chroma import Chroma
from langchain_core.prompts import PromptTemplate
try:
    from langchain.chains import RetrievalQA
except ImportError:
    from langchain_classic.chains import RetrievalQA

# Load env variables
load_dotenv()

# Set DB_DIR dynamically at the top (Fix 1)
api_key = os.getenv("OPENAI_API_KEY")
DB_DIR = "./chroma_db_openai" if (api_key and api_key != "your_openai_api_key_here") else "./chroma_db_local"

# App Page Configurations (Update 2)
st.set_page_config(
    page_title="Mumbai Metropolitan Real Estate Assistant",
    page_icon="🏢",
    layout="wide"
)

# Custom Premium Styling (Fix 2 - unsafe_allow_html)
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
""", unsafe_allow_html=True)

# App Title & Subtitle (Update 2)
st.title("🏢 Mumbai Metropolitan Real Estate Assistant")
st.markdown("### AI Agent covering Mumbai City · Western & Central Suburbs · Thane · Navi Mumbai")

# MMR Localities mapping by Zone (Update 1)
ZONE_LOCALITIES = {
    "Central Eastern Suburbs": ["Kanjurmarg", "Bhandup", "Mulund", "Vikhroli", "Nahur"],
    "Central Mumbai": ["Dadar", "Kurla", "Ghatkopar", "Chembur", "Govandi", "Mankhurd", "Tilak Nagar"],
    "Western Mumbai": ["Andheri", "Borivali", "Kandivali", "Malad", "Goregaon", "Dahisar", "Mira Road", "Bhayandar"],
    "South & Harbour Mumbai": ["Bandra", "Worli", "Lower Parel", "Parel", "Wadala", "Sion", "Matunga", "Mahim"],
    "Thane District": ["Thane West", "Thane East", "Kalyan", "Dombivli", "Ulhasnagar", "Bhiwandi", "Ambernath", "Badlapur"],
    "Navi Mumbai": ["Vashi", "Kharghar", "Panvel", "Airoli", "Nerul", "Belapur", "Sanpada", "Ghansoli", "Kopar Khairane"]
}

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
            # Re-evaluate DB path
            DB_DIR = "./chroma_db_openai" if (api_key and api_key != "your_openai_api_key_here") else "./chroma_db_local"
    else:
        st.success("🔑 OpenAI API Key loaded from .env")
        
    st.subheader("Filter Settings")
    
    # Two-level filter (Update 1)
    zone_list = ["All Zones"] + list(ZONE_LOCALITIES.keys())
    selected_zone = st.selectbox("Focus Zone:", zone_list)
    
    if selected_zone == "All Zones":
        selected_locality = "All"
        st.selectbox("Focus Locality:", ["All"], disabled=True)
    else:
        localities = ["All"] + ZONE_LOCALITIES[selected_zone]
        selected_locality = st.selectbox("Focus Locality:", localities)
    
    # Sidebar Info Text (Update 3)
    st.info(
        "This chatbot uses Retrieval Augmented Generation (RAG). "
        "It retrieves local market knowledge across 6 Mumbai Metropolitan zones "
        "(Central Eastern, Central Mumbai, Western Mumbai, South & Harbour, Thane, and Navi Mumbai) "
        "to ensure accurate, hallucination-free answers."
    )

# Vector store connection with Dual-mode embedding logic
@st.cache_resource
def get_vector_store(db_path):
    api_key = os.getenv("OPENAI_API_KEY")
    use_openai = api_key and api_key != "your_openai_api_key_here" and api_key != ""
    
    try:
        if use_openai:
            embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        else:
            from langchain_community.embeddings import HuggingFaceEmbeddings
            embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
            
        vectorstore = Chroma(
            collection_name="mumbai_realestate",
            embedding_function=embeddings,
            persist_directory=db_path
        )
        return vectorstore
    except Exception as e:
        st.error(f"Error loading Vector Store: {e}")
        return None

# Check if vector DB is initialized
vectorstore = get_vector_store(DB_DIR)

# System Prompt Template (Update 5)
PROMPT_TEMPLATE = """You are an expert real estate consultant covering the full Mumbai Metropolitan Region including Mumbai City (Central, Western, Harbour lines), Eastern Suburbs, Thane District, and Navi Mumbai. You have deep knowledge of all micro-markets, connectivity, RERA filings, pricing trends, and upcoming infrastructure across the MMR.
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

# Chat input (Update 4)
if user_query := st.chat_input("Ask about any locality — prices, projects, metro, connectivity, RERA status..."):
    # 1. Show user message
    st.session_state.messages.append({"role": "user", "content": user_query})
    with st.chat_message("user"):
        st.write(user_query)

    # 2. Process query with RAG
    if not vectorstore:
        with st.chat_message("assistant"):
            st.error("Vector Database not found. Please run `python ingest.py` first to index your documents.")
    else:
        with st.chat_message("assistant"):
            with st.spinner("Analyzing market data..."):
                try:
                    # Construct search arguments with dynamic metadata filter (Fix 3 & UI Update 1)
                    search_kwargs = {"k": 4}
                    
                    if selected_zone != "All Zones":
                        if selected_locality != "All":
                            # Specific locality filter (Fix 3: explicit operator form)
                            search_kwargs["filter"] = {"locality": {"$eq": selected_locality.lower()}}
                        else:
                            # Filter by all localities in the selected zone (Fix 3: explicit operator form)
                            search_kwargs["filter"] = {
                                "locality": {
                                    "$in": [loc.lower() for loc in ZONE_LOCALITIES[selected_zone]]
                                }
                            }

                    retriever = vectorstore.as_retriever(search_kwargs=search_kwargs)
                    
                    # Dual-mode LLM logic
                    api_key = os.getenv("OPENAI_API_KEY")
                    use_openai = api_key and api_key != "your_openai_api_key_here" and api_key != ""
                    
                    if use_openai:
                        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
                    else:
                        from langchain_community.llms import Ollama
                        llm = Ollama(model="llama3", temperature=0)
                    
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
                    if not use_openai:
                        answer_display = f"🤖 **[Local Offline AI Mode]**\n\n{answer}"
                    else:
                        answer_display = answer
                        
                    st.write(answer_display)
                    
                    if sources:
                        with st.expander("Show Sources Referenced"):
                            for source in sources:
                                st.caption(f"📄 Source File: {source}")
                                
                    # Save to session history
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": answer_display,
                        "sources": sources
                    })
                    
                except Exception as e:
                    st.error(f"An error occurred: {e}")
