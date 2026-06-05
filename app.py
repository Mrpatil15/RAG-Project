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

# Custom Premium Styling & Import Fonts
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');
    @import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css');

    /* Global Base Styling */
    html, body, [data-testid="stAppViewContainer"], .main {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        background-color: #070a13 !important;
        background-image: 
            radial-gradient(circle at 10% 20%, rgba(59, 130, 246, 0.08) 0%, transparent 40%),
            radial-gradient(circle at 90% 80%, rgba(139, 92, 246, 0.08) 0%, transparent 40%) !important;
        color: #f8fafc !important;
    }

    /* Hide standard Streamlit header clutter */
    [data-testid="stHeader"] {
        background-color: rgba(7, 10, 19, 0.5) !important;
        backdrop-filter: blur(20px) !important;
        border-bottom: 1px solid rgba(51, 65, 85, 0.2) !important;
    }

    /* Style the decoration line */
    [data-testid="stDecoration"] {
        background-image: linear-gradient(90deg, #3b82f6, #8b5cf6) !important;
    }

    /* Sidebar Frosted Glassmorphism */
    [data-testid="stSidebar"] {
        background-color: rgba(13, 20, 38, 0.6) !important;
        backdrop-filter: blur(25px) !important;
        -webkit-backdrop-filter: blur(25px) !important;
        border-right: 1px solid rgba(51, 65, 85, 0.3) !important;
    }

    /* Sidebar Labels */
    [data-testid="stSidebar"] label {
        font-family: 'Outfit', sans-serif !important;
        font-size: 11px !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        letter-spacing: 1.5px !important;
        color: #64748b !important;
        margin-bottom: 8px !important;
        display: flex !important;
        align-items: center !important;
        gap: 6px !important;
    }

    /* Custom styles for Streamlit selectbox and input controls */
    div[data-baseweb="select"] {
        background-color: rgba(10, 15, 30, 0.7) !important;
        border: 1px solid rgba(51, 65, 85, 0.4) !important;
        border-radius: 12px !important;
        transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1) !important;
    }
    div[data-baseweb="select"]:hover {
        border-color: rgba(59, 130, 246, 0.5) !important;
        background-color: rgba(10, 15, 30, 0.9) !important;
    }
    div[data-baseweb="select"]:focus-within {
        border-color: #3b82f6 !important;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2), 0 0 15px rgba(59, 130, 246, 0.1) !important;
    }
    div[data-baseweb="select"] * {
        color: #f8fafc !important;
    }

    /* Inputs style */
    div[data-testid="stTextInput"] input {
        background-color: rgba(10, 15, 30, 0.7) !important;
        border: 1px solid rgba(51, 65, 85, 0.4) !important;
        border-radius: 12px !important;
        color: #f8fafc !important;
        transition: all 0.3s ease !important;
    }
    div[data-testid="stTextInput"] input:hover {
        border-color: rgba(59, 130, 246, 0.5) !important;
        background-color: rgba(10, 15, 30, 0.9) !important;
    }
    div[data-testid="stTextInput"] input:focus {
        border-color: #3b82f6 !important;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2) !important;
    }

    /* Streamlit Alert Card Overrides */
    .stAlert {
        background-color: rgba(25, 40, 72, 0.2) !important;
        border: 1px solid rgba(51, 65, 85, 0.3) !important;
        border-radius: 16px !important;
        padding: 16px !important;
        box-shadow: inset 0 0 12px rgba(255, 255, 255, 0.02) !important;
    }
    .stAlert * {
        color: #cbd5e1 !important;
    }

    /* Chat Messages Layout */
    .chat-message-wrapper {
        display: flex;
        gap: 16px;
        margin-bottom: 24px;
        max-width: 85%;
        animation: slideUp 0.4s cubic-bezier(0.16, 1, 0.3, 1);
    }
    .chat-message-wrapper.user {
        margin-left: auto;
        flex-direction: row-reverse;
    }
    .chat-message-wrapper.assistant {
        margin-right: auto;
    }
    @keyframes slideUp {
        from {
            opacity: 0;
            transform: translateY(16px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    /* Avatars */
    .message-avatar {
        width: 42px;
        height: 42px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 16px;
        flex-shrink: 0;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
    }
    .user-avatar {
        background: linear-gradient(135deg, #3b82f6, #8b5cf6);
        border: 1px solid rgba(139, 92, 246, 0.3);
        color: white;
    }
    .assistant-avatar {
        background: linear-gradient(135deg, #10b981, #059669);
        border: 1px solid rgba(16, 185, 129, 0.3);
        color: white;
    }

    /* Message bubble */
    .message-content {
        background-color: rgba(20, 30, 54, 0.4);
        border: 1px solid rgba(51, 65, 85, 0.4);
        border-radius: 18px;
        padding: 16px 22px;
        line-height: 1.65;
        font-size: 15px;
        color: #cbd5e1;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    }
    .user-content {
        border-top-right-radius: 4px;
        background-color: rgba(59, 130, 246, 0.08);
        border-color: rgba(59, 130, 246, 0.2);
        color: #f8fafc;
    }
    .assistant-content {
        border-top-left-radius: 4px;
    }
    .message-content strong {
        color: #f8fafc;
        font-weight: 600;
    }

    /* Sources Referenced Tags */
    .sources-container {
        margin-top: 14px;
        padding-top: 10px;
        border-top: 1px solid rgba(255, 255, 255, 0.06);
    }
    .sources-title {
        font-size: 12px;
        color: #64748b;
        font-weight: 600;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .sources-tags {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
    }
    .source-tag {
        font-size: 11px;
        font-weight: 600;
        color: #10b981;
        background-color: rgba(16, 185, 129, 0.08);
        border: 1px solid rgba(16, 185, 129, 0.15);
        padding: 4px 10px;
        border-radius: 6px;
        display: inline-flex;
        align-items: center;
        gap: 6px;
        transition: all 0.2s;
    }
    .source-tag:hover {
        background-color: rgba(16, 185, 129, 0.15);
        border-color: rgba(16, 185, 129, 0.3);
        transform: translateY(-1px);
    }

    /* Chat Input Overrides */
    div[data-testid="stChatInput"] {
        padding-bottom: 24px !important;
    }
    div[data-testid="stChatInput"] textarea {
        background-color: rgba(10, 15, 30, 0.8) !important;
        border: 1px solid rgba(51, 65, 85, 0.4) !important;
        border-radius: 16px !important;
        color: #f8fafc !important;
        padding: 14px 18px !important;
        font-size: 15px !important;
        transition: all 0.3s ease !important;
    }
    div[data-testid="stChatInput"] textarea:focus {
        border-color: #3b82f6 !important;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15) !important;
    }

    /* Custom Header Styles */
    .header-container {
        margin-bottom: 30px;
        border-bottom: 1px solid rgba(51, 65, 85, 0.2);
        padding-bottom: 20px;
    }
    .title-container {
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .title-icon {
        font-size: 32px;
    }
    .gradient-title {
        font-family: 'Outfit', sans-serif;
        font-size: 30px;
        font-weight: 700;
        margin: 0;
        background: linear-gradient(135deg, #3b82f6, #8b5cf6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0 2px 10px rgba(59, 130, 246, 0.1);
    }
    .subtitle-text {
        color: #94a3b8;
        font-size: 15px;
        margin-top: 8px;
    }

    /* Sidebar Logo & Status Card */
    .sidebar-logo {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 28px;
        padding-bottom: 16px;
        border-bottom: 1px solid rgba(51, 65, 85, 0.2);
    }
    .sidebar-logo i {
        font-size: 24px;
        background: linear-gradient(135deg, #60a5fa, #a78bfa);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        filter: drop-shadow(0 0 8px rgba(96, 165, 250, 0.3));
    }
    .sidebar-logo span {
        font-family: 'Outfit', sans-serif;
        font-weight: 700;
        font-size: 18px;
        letter-spacing: 0.8px;
        background: linear-gradient(135deg, #3b82f6, #8b5cf6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .sidebar-status-card {
        background-color: rgba(25, 40, 72, 0.2);
        border: 1px solid rgba(51, 65, 85, 0.3);
        border-radius: 16px;
        padding: 16px;
        margin-top: 24px;
    }
    .status-indicator {
        display: flex;
        align-items: center;
        gap: 10px;
        font-size: 13px;
        font-weight: 600;
        color: #cbd5e1;
        margin-bottom: 8px;
    }
    .pulse-dot {
        width: 8px;
        height: 8px;
        background-color: #10b981;
        border-radius: 50%;
        box-shadow: 0 0 8px #10b981;
        position: relative;
    }
    .pulse-dot::after {
        content: '';
        position: absolute;
        width: 100%;
        height: 100%;
        background-color: inherit;
        border-radius: inherit;
        animation: ripple 2s infinite ease-out;
    }
    @keyframes ripple {
        0% { transform: scale(1); opacity: 0.8; }
        100% { transform: scale(2.8); opacity: 0; }
    }
    .mode-indicator {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 12px;
        font-weight: 500;
        padding: 6px 12px;
        border-radius: 8px;
        width: fit-content;
    }
    .mode-openai {
        color: #60a5fa;
        background-color: rgba(59, 130, 246, 0.08);
        border: 1px solid rgba(59, 130, 246, 0.15);
    }
    .mode-local {
        color: #a78bfa;
        background-color: rgba(139, 92, 246, 0.08);
        border: 1px solid rgba(139, 92, 246, 0.15);
    }
    </style>
""", unsafe_allow_html=True)

# Helper functions for Custom Chat Rendering
def markdown_to_html(text):
    import re
    # 1. Escape HTML entities
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    
    # 2. Convert bold formatting: **text** -> <strong>text</strong>
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
    
    # 3. Convert italic formatting: *text* -> <em>text</em>
    text = re.sub(r'(?<!\n)\*(?!\s)(.*?)\*', r'<em>\1</em>', text)
    
    # 4. Convert bullet points: lines starting with "- " or "* "
    lines = text.split('\n')
    in_list = False
    formatted_lines = []
    
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("- ") or stripped.startswith("* "):
            if not in_list:
                formatted_lines.append('<ul style="margin: 4px 0 12px 20px; padding-left: 0;">')
                in_list = True
            content = stripped[2:]
            formatted_lines.append(f'<li style="margin-bottom: 4px;">{content}</li>')
        else:
            if in_list:
                formatted_lines.append('</ul>')
                in_list = False
            formatted_lines.append(line)
            
    if in_list:
        formatted_lines.append('</ul>')
        
    text = '\n'.join(formatted_lines)
    # 5. Convert line breaks (newlines) to <br> tags
    text = text.replace('\n', '<br>')
    return text

def render_message(role, content, sources=None):
    avatar_html = ""
    bubble_class = ""
    avatar_class = ""
    
    if role == "user":
        avatar_html = '<i class="fa-solid fa-user"></i>'
        bubble_class = "user-content"
        avatar_class = "user-avatar"
    else:
        avatar_html = '<i class="fa-solid fa-robot"></i>'
        bubble_class = "assistant-content"
        avatar_class = "assistant-avatar"
        
    html_content = markdown_to_html(content)
    
    sources_html = ""
    if sources:
        tags_html = "".join([f'<span class="source-tag"><i class="fa-solid fa-file-invoice"></i> {s}</span>' for s in sources])
        sources_html = f"""
        <div class="sources-container">
            <div class="sources-title"><i class="fa-solid fa-book-open"></i> Sources Referenced:</div>
            <div class="sources-tags">
                {tags_html}
            </div>
        </div>
        """
        
    st.markdown(f"""
        <div class="chat-message-wrapper {role}">
            <div class="message-avatar {avatar_class}">{avatar_html}</div>
            <div class="message-content {bubble_class}">
                {html_content}
                {sources_html}
            </div>
        </div>
    """, unsafe_allow_html=True)

# Custom Premium Header
st.markdown("""
    <div class="header-container">
        <div class="title-container">
            <span class="title-icon">🏢</span>
            <h1 class="gradient-title">Mumbai Metropolitan Real Estate Assistant</h1>
        </div>
        <p class="subtitle-text">AI Agent covering Mumbai City · Western & Central Suburbs · Thane · Navi Mumbai</p>
    </div>
""", unsafe_allow_html=True)

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
    # Custom Sidebar Logo
    st.markdown("""
        <div class="sidebar-logo">
            <i class="fa-solid fa-building-circle-check"></i>
            <span>MUMBAI REALTY</span>
        </div>
    """, unsafe_allow_html=True)
    
    # Check if API Key is available
    api_key = os.getenv("OPENAI_API_KEY")
    use_openai = api_key and api_key != "your_openai_api_key_here" and api_key != ""
    
    if not api_key or api_key == "your_openai_api_key_here":
        st.warning("⚠️ OpenAI API Key not found in .env file.")
        user_key = st.text_input("Enter OpenAI API Key:", type="password")
        if user_key:
            os.environ["OPENAI_API_KEY"] = user_key
            st.success("API Key applied locally!")
            api_key = user_key
            use_openai = True
            # Re-evaluate DB path
            DB_DIR = "./chroma_db_openai" if (api_key and api_key != "your_openai_api_key_here") else "./chroma_db_local"
    else:
        st.success("🔑 OpenAI API Key loaded")
        
    st.markdown("### <i class='fa-solid fa-filter' style='color:#3b82f6;margin-right:6px;'></i> Filters", unsafe_allow_html=True)
    
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
        "to ensure accurate, hallucination-free answers."
    )
    
    # Custom Sidebar Status Indicator
    mode_name = "Online Mode (OpenAI GPT-4o)" if use_openai else "Offline Mode (Local Llama3)"
    mode_class = "mode-openai" if use_openai else "mode-local"
    mode_icon = "fa-solid fa-cloud" if use_openai else "fa-solid fa-hard-drive"
    
    st.markdown(f"""
        <div class="sidebar-status-card">
            <div class="status-indicator">
                <div class="pulse-dot"></div>
                <span>AI Engine Status</span>
            </div>
            <div class="mode-indicator {mode_class}">
                <i class="{mode_icon}"></i>
                <span>{mode_name}</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

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
    render_message(msg["role"], msg["content"], msg.get("sources"))

# Chat input (Update 4)
if user_query := st.chat_input("Ask about any locality — prices, projects, metro, connectivity, RERA status..."):
    # 1. Show user message
    st.session_state.messages.append({"role": "user", "content": user_query})
    render_message("user", user_query)

    # 2. Process query with RAG
    if not vectorstore:
        render_message("assistant", "❌ Vector Database not found. Please run `python ingest.py` first to index your documents.")
    else:
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
                    
                render_message("assistant", answer_display, sources)
                            
                # Save to session history
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer_display,
                    "sources": sources
                })
                
                # Trigger rerun to show layout correctly
                st.rerun()
                
            except Exception as e:
                st.error(f"An error occurred: {e}")
