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
Rename `.env.example` to `.env` and configure your API key to run in Cloud mode:
```env
OPENAI_API_KEY=your_openai_key
```
*If you leave it commented out, the chatbot will run locally using Ollama and HuggingFace.*

### 3. Ingest Documents
Run the ingestion script to parse and index the locality briefs:
```bash
python ingest.py
```

### 4. Launch the Streamlit App
Run the Streamlit frontend:
```bash
streamlit run app.py
```
Open the local URL (typically `http://localhost:8501`) in your browser to interact with the assistant.
