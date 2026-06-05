# 🏢 Mumbai Metropolitan Real Estate RAG Assistant

An enterprise-grade Retrieval-Augmented Generation (RAG) conversational agent specialized in the **Mumbai Metropolitan Region (MMR)** real estate markets. Built using **LangChain**, **FastAPI**, **Streamlit**, and **ChromaDB**, it implements double-level metadata filtering (Zone & Locality) for highly specific, hallucination-free localized analytics.

---

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/FastAPI-0.100+-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/LangChain-0.2+-13aa52?style=for-the-badge" alt="LangChain" />
  <img src="https://img.shields.io/badge/Streamlit-1.22+-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white" alt="Streamlit" />
  <img src="https://img.shields.io/badge/VectorDB-ChromaDB-blue?style=for-the-badge" alt="ChromaDB" />
</p>

---

## 🏗️ System Architecture

The chatbot utilizes semantic search coupled with strict metadata filtering on the vector index level to query local real estate knowledge documents.

```mermaid
graph TD
    User[User Client] -->|1. Query + Filters| UI[App Interface: Web / Streamlit]
    UI -->|2. Retrieve Chunks with Explicit Metadata Filter| DB[(ChromaDB Vector Store)]
    DB -->|3. Matched Document Chunks| Chain[RetrievalQA Chain]
    Chain -->|4. Prompt + Context Injection| LLM[LLM Engine: OpenAI GPT-4o-mini / Ollama Llama3]
    LLM -->|5. Structured Answer| Chain
    Chain -->|6. Format Answer & Cited Sources| UI
    UI -->|7. Render Chat Bubbles & Source Tags| User

    style DB fill:#1e293b,stroke:#3b82f6,stroke-width:2px;
    style LLM fill:#1e293b,stroke:#10b981,stroke-width:2px;
    style UI fill:#0f172a,stroke:#8b5cf6,stroke-width:2px;
```

---

## 🗺️ Region & Zone Index Coverage

The knowledge base compiles comprehensive regional market briefs, covering connectivity infrastructure (Metro lines, Coastal Road, MTHL), key developer projects, pricing brackets, and upcoming growth catalysts.

| Zone | Primary Localities Covered | RAG Metadata Filter |
| :--- | :--- | :--- |
| **Central Eastern Suburbs** | Kanjurmarg, Bhandup, Mulund, Vikhroli, Nahur | `locality: [locality_name]` |
| **Central Mumbai** | Dadar, Kurla, Ghatkopar, Chembur, Govandi, Mankhurd, Tilak Nagar | `locality: [locality_name]` |
| **Western Mumbai** | Andheri, Borivali, Kandivali, Malad, Goregaon, Dahisar, Mira Road, Bhayandar | `locality: [locality_name]` |
| **South & Harbour Mumbai** | Bandra, Worli, Lower Parel, Parel, Wadala, Sion, Matunga, Mahim | `locality: [locality_name]` |
| **Thane District** | Thane West, Thane East, Kalyan, Dombivli, Ulhasnagar, Bhiwandi, Ambernath, Badlapur | `locality: [locality_name]` |
| **Navi Mumbai** | Vashi, Kharghar, Panvel, Airoli, Nerul, Belapur, Sanpada, Ghansoli, Kopar Khairane | `locality: [locality_name]` |

---

## 🛠️ Core Capabilities

- **Dual-Mode Inference**:
  - *Cloud Inference*: Uses OpenAI `text-embedding-3-small` and `gpt-4o-mini` if `OPENAI_API_KEY` is present.
  - *Local/Offline Inference*: Fallback to HuggingFace `sentence-transformers/all-MiniLM-L6-v2` and local **Ollama** running `llama3`.
- **Explicit Operator Metadata Querying**: Implements strict vector indexing filters (`$eq` for specific localities and `$in` for full-zone queries) to guarantee zero-context hallucinations.
- **Browser-Side Chat Session History**: Local storage integration ensures the chat session persists between refreshes.

---

## 📂 Project Structure

```
.
├── data/
│   └── locality_briefs/      # Regional real estate markdown files
├── chroma_db_openai/         # Chroma DB storage for OpenAI embeddings (1536 dim)
├── chroma_db_local/          # Chroma DB storage for HuggingFace embeddings (384 dim)
├── frontend/                 # Static frontend files for FastAPI server
│   ├── index.html            # Web interface layout
│   ├── style.css             # Glassmorphic visual theme
│   └── app.js                # Local storage history and API connectors
├── app.py                    # Streamlit Dashboard application
├── server.py                 # FastAPI Web Server backend
├── ingest.py                 # Indexing and database creation script
├── requirements.txt          # Python dependencies
└── .env                      # Credentials file (git-ignored)
```

---

## 🚀 Setup & Execution

### 1. Installation
Install project dependencies:
```bash
pip install -r requirements.txt
```

### 2. Configure Credentials (Optional)
Create a `.env` file at the root directory and add your key for Cloud Mode:
```env
OPENAI_API_KEY=your_openai_api_key_here
```
*If left empty, the application runs fully locally using Ollama Llama-3.*

### 3. Database Ingestion
Index the locality briefs into the vector database:
```bash
python ingest.py
```

---

## 🖥️ Choose Your UI Client

You can run either client interface depending on your requirements:

### **Interface A: FastAPI Web Application (Recommended)**
A fast HTML5/CSS3/JS single-page application, featuring persistent chat history and optimized pre-cached retrieval speeds.
- **Run Server**:
  ```bash
  python server.py
  ```
- **Access Link**: [http://localhost:8000](http://localhost:8000)

### **Interface B: Streamlit Dashboard**
A Python-driven dashboard styled with custom CSS overrides, glassmorphism, and active engine indicators.
- **Run Server**:
  ```bash
  streamlit run app.py
  ```
- **Access Link**: [http://localhost:8501](http://localhost:8501)

---

## 🐳 Dockerization & 24/7 Cloud Deployment

To deploy this application to the cloud and run it 24/7 without needing your local machine active, you can use the provided `Dockerfile`.

### 1. Run via Docker Locally
To build and run the container on your local machine:
```bash
docker build -t mumbai-realty-rag .
docker run -p 7860:7860 --env OPENAI_API_KEY="your_api_key" -d mumbai-realty-rag
```
After launching, the app will be accessible at [http://localhost:7860](http://localhost:7860).

### 2. Deploy 24/7 to Hugging Face Spaces (Free & Recommended)
You can host this application permanently on **Hugging Face Spaces** for free:
1. Go to [huggingface.co/spaces](https://huggingface.co/spaces) and click **Create new Space**.
2. Name your space (e.g. `mumbai-realty-rag`) and select **Docker** as the SDK.
3. Select **Blank** under the Docker template (do not choose any preset).
4. Under **Settings** -> **Repository**, link your GitHub Repository `Mrpatil15/RAG-Project` (or configure it as a Git remote and push directly to Hugging Face).
5. If using OpenAI Cloud Mode, go to **Settings** -> **Variables and Secrets**, add a new Secret with name `OPENAI_API_KEY` and paste your key.
6. Hugging Face will automatically build your Docker container, download the local embedding model weights, compile the vector store, and deploy your live assistant!

### 3. Deploy to Render.com (Free Tier Alternative)
1. Register/Login on [Render.com](https://render.com).
2. Click **New** -> **Web Service** and connect your GitHub Repository `Mrpatil15/RAG-Project`.
3. Render will auto-detect the `Dockerfile` and select Docker environment.
4. In the service settings, add `OPENAI_API_KEY` under the Environment variables tab if using OpenAI.
5. Deploy the service. It will expose port 7860 automatically.

