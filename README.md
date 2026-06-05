# Mumbai Metropolitan Real Estate Assistant

An advanced Retrieval-Augmented Generation (RAG) chatbot built with LangChain, Streamlit, and ChromaDB, covering the full **Mumbai Metropolitan Region (MMR)**.

---

## 🗺️ Region & Zone Coverage

The chatbot has been updated to cover **6 major zones** across the MMR:

### **Zone 1: Central Eastern Suburbs**
* Localities: Kanjurmarg, Bhandup, Mulund, Vikhroli, Nahur

### **Zone 2: Central Mumbai (Central Railway Line)**
* Localities: Dadar, Kurla, Ghatkopar, Chembur, Govandi, Mankhurd, Tilak Nagar

### **Zone 3: Western Mumbai (Western Railway Line)**
* Localities: Andheri, Borivali, Kandivali, Malad, Goregaon, Dahisar, Mira Road, Bhayandar

### **Zone 4: South & Harbour Mumbai**
* Localities: Bandra, Worli, Lower Parel, Parel, Wadala, Sion, Matunga, Mahim

### **Zone 5: Thane District**
* Localities: Thane West, Thane East, Kalyan, Dombivli, Ulhasnagar, Bhiwandi, Ambernath, Badlapur

### **Zone 6: Navi Mumbai**
* Localities: Vashi, Kharghar, Panvel, Airoli, Nerul, Belapur, Sanpada, Ghansoli, Kopar Khairane

---

## 🛠️ Key Features

1. **Dual-Mode Embedding & LLM Logic:**
   * **Cloud Mode:** Runs using OpenAI `text-embedding-3-small` and `gpt-4o-mini` if `OPENAI_API_KEY` is present in your `.env`.
   * **Local/Offline Mode:** Automatically falls back to HuggingFace `sentence-transformers/all-MiniLM-L6-v2` and local **Ollama** running `Llama-3` (no API key required).
2. **Two-Level Filter:**
   * Filter queries by selecting a **Zone** and a specific **Locality** dynamically in the sidebar.
3. **Explicit Operator Filtering:**
   * Metadata filtering uses explicit ChromaDB operators (`$eq` for single locality queries and `$in` for full-zone queries).

---

## 📂 Project Structure

```
.
├── data/
│   └── locality_briefs/      # Markdown files containing regional data
├── chroma_db_openai/         # Chroma DB storage for OpenAI embeddings (1536 dim)
├── chroma_db_local/          # Chroma DB storage for HuggingFace embeddings (384 dim)
├── app.py                    # Streamlit web application
├── server.py                 # Alternative FastAPI web server
├── ingest.py                 # Indexing and database creation script
├── requirements.txt          # Python dependencies
└── .env                      # Local credentials (git-ignored)
```

---

## 🚀 Setup & Execution

### 1. Installation
Install all requirements:
```bash
pip install -r requirements.txt
```

### 2. Set Up Environment Variables (Optional)
Create a `.env` file and configure your API key to run in OpenAI Cloud mode:
```env
OPENAI_API_KEY=your_openai_key
```
*If you do not set an OpenAI API key, the system automatically falls back to local HuggingFace embeddings and Ollama (Llama-3).*

### 3. Ingest Documents
Run the indexing script to parse all local markdown briefs and create the vector stores:
```bash
python ingest.py
```

---

## 🖥️ Choosing Your Application Interface

The project includes two highly polished application interfaces. You can run either (or both concurrently):

### **Interface A: FastAPI Single-Page Web Application**
A fast, single-page application built on raw HTML/CSS/JS, featuring persistent local storage chat history and cached global startup retrieval.
* **Launch Command**:
  ```bash
  python server.py
  ```
* **Local Web Link**: [http://localhost:8000](http://localhost:8000)
* **Key Features**:
  * Persistent chat history (survives browser refreshes).
  * 10x faster response latency due to preloaded startup vectors.
  * Dynamic two-level filters and clean responsive layouts.

### **Interface B: Streamlit Chatbot Dashboard**
A Python-driven dashboard styled with custom CSS overrides, glassmorphism, and a status badge card.
* **Launch Command**:
  ```bash
  streamlit run app.py
  ```
* **Local Web Link**: [http://localhost:8501](http://localhost:8501)
* **Key Features**:
  * Custom styled conversation bubbles (user aligns right, assistant aligns left).
  * Custom sidebar logo and active AI engine badge.

