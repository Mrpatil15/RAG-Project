import os
import glob
from dotenv import load_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

# Load environment variables
load_dotenv()

DATA_DIR = "./data/locality_briefs"
DB_DIR = "./chroma_db"

def ingest_documents():
    # 1. Check API Key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "your_openai_api_key_here":
        print("[WARNING] OPENAI_API_KEY is not set in your .env file!")
        print("Please configure your .env file with a valid OpenAI API key before running ingestion.")
        return

    print("Initializing OpenAI Embeddings...")
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    # 2. Find and load all locality briefs
    markdown_files = glob.glob(os.path.join(DATA_DIR, "*.md"))
    if not markdown_files:
        print(f"No markdown briefs found in {DATA_DIR}. Please add some first.")
        return

    documents = []
    print(f"Loading files from {DATA_DIR}...")
    
    for file_path in markdown_files:
        file_name = os.path.basename(file_path)
        locality_name = os.path.splitext(file_name)[0].lower() # e.g. 'kanjurmarg'
        
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
    print(f"Saving embeddings to local Chroma DB directory: {DB_DIR}...")
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=DB_DIR,
        collection_name="mumbai_realestate"
    )
    
    print("Ingestion completed successfully!")

if __name__ == "__main__":
    ingest_documents()
