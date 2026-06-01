import os
import glob
from dotenv import load_dotenv
try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:
    from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_chroma import Chroma

# Load environment variables
load_dotenv()

DATA_DIR = "./data/locality_briefs"

def ingest_documents():
    api_key = os.getenv("OPENAI_API_KEY")
    use_openai = api_key and api_key != "your_openai_api_key_here"

    # 1. Initialize Embeddings & Set Collection Target
    if use_openai:
        print("[MODE] OpenAI API Key detected. Using OpenAI Cloud Embeddings.")
        from langchain_openai import OpenAIEmbeddings
        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        db_dir = "./chroma_db_openai"
    else:
        print("[MODE] No OpenAI key detected. Using local HuggingFace Offline Embeddings (sentence-transformers)...")
        from langchain_community.embeddings import HuggingFaceEmbeddings
        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        db_dir = "./chroma_db_local"

    # 2. Find and load all locality briefs
    markdown_files = glob.glob(os.path.join(DATA_DIR, "*.md"))
    if not markdown_files:
        print(f"No markdown briefs found in {DATA_DIR}. Please add some first.")
        return

    documents = []
    print(f"Loading files from {DATA_DIR}...")
    
    for file_path in markdown_files:
        file_name = os.path.basename(file_path)
        locality_name = os.path.splitext(file_name)[0].lower()
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        doc = Document(
            page_content=content,
            metadata={
                "source": file_name,
                "locality": locality_name
            }
        )
        documents.append(doc)
        print(f" - Loaded {file_name} (locality: {locality_name})")

    # 3. Chunk documents
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        length_function=len,
        add_start_index=True
    )
    
    chunks = text_splitter.split_documents(documents)
    print(f"Split {len(documents)} documents into {len(chunks)} text chunks.")

    # 4. Save to Chroma DB
    print(f"Saving embeddings to local Chroma DB directory: {db_dir}...")
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=db_dir,
        collection_name="mumbai_realestate"
    )
    
    print("Ingestion completed successfully!")

if __name__ == "__main__":
    ingest_documents()
