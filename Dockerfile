FROM python:3.10-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/home/user/.cache/huggingface

# Set up working directory
WORKDIR /code

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create user with UID 1000 for security/compatibility (Hugging Face requirement)
RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:${PATH}"

WORKDIR /home/user/app

# Copy requirements and install
COPY --chown=user:user requirements.txt .
RUN pip install --user --upgrade pip && \
    pip install --user -r requirements.txt

# Copy the rest of the application files
COPY --chown=user:user . .

# Run ingestion during docker build phase to download sentence-transformers model
# and compile local Chroma vector database
RUN python ingest.py

# Expose the default Hugging Face Spaces port
EXPOSE 7860

# Run FastAPI backend via Uvicorn
CMD ["python", "-m", "uvicorn", "server:app", "--host", "0.0.0.0", "--port", "7860"]
