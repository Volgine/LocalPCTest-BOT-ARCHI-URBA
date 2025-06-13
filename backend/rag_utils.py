import json
from pathlib import Path
from typing import List

import faiss
import httpx
from sentence_transformers import SentenceTransformer
import PyPDF2
from dotenv import load_dotenv

load_dotenv()

# Embedding model
MODEL_NAME = "all-MiniLM-L6-v2"
model = SentenceTransformer(MODEL_NAME)
EMBED_DIM = model.get_sentence_embedding_dimension()

# Paths for persistence
INDEX_PATH = Path("faiss.index")
DOCS_PATH = Path("faiss_docs.json")

# Load or initialize index
if INDEX_PATH.exists():
    index = faiss.read_index(str(INDEX_PATH))
    if DOCS_PATH.exists():
        documents = json.loads(DOCS_PATH.read_text())
    else:
        documents = []
else:
    index = faiss.IndexFlatL2(EMBED_DIM)
    documents = []


def _save_state() -> None:
    """Persist the FAISS index and documents to disk."""
    faiss.write_index(index, str(INDEX_PATH))
    DOCS_PATH.write_text(json.dumps(documents))


def _extract_text(path: str) -> str:
    """Extract text from a txt or PDF file."""
    if path.lower().endswith(".pdf"):
        text = ""
        with open(path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text
    else:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()


def _chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """Split text into overlapping chunks."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap
    return chunks


def ingest_documents(path: str) -> None:
    """Load documents from a file or directory and add them to the FAISS index."""
    p = Path(path)
    files = []
    if p.is_dir():
        for file in p.glob("**/*"):
            if file.suffix.lower() in {".txt", ".pdf"}:
                files.append(file)
    else:
        if p.suffix.lower() in {".txt", ".pdf"}:
            files.append(p)

    for file in files:
        text = _extract_text(str(file))
        if not text.strip():
            continue
        chunks = _chunk_text(text)
        if not chunks:
            continue
        vectors = model.encode(chunks)
        index.add(vectors.astype("float32"))
        documents.extend(chunks)

    if files:
        _save_state()


def retrieve_context(question: str, top_k: int = 5) -> List[str]:
    """Return the most relevant snippets for a question."""
    if index.ntotal == 0:
        return []
    vector = model.encode([question]).astype("float32")
    distances, idx = index.search(vector, top_k)
    snippets = [documents[i] for i in idx[0] if i < len(documents)]
    return snippets


async def generate_llm_answer(question: str, context: str, api_key: str) -> str:
    """Call the Groq API using httpx and return the answer."""
    if not api_key:
        return ""

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}"}

    messages = [
        {
            "role": "system",
            "content": (
                "Tu es un assistant expert en urbanisme et architecture. "
                "Utilise le contexte fourni pour r\u00e9pondre de mani\u00e8re pr\u00e9cise."
            ),
        }
    ]
    if context:
        messages.append({"role": "user", "content": f"Contexte:\n{context}\n\nQuestion: {question}"})
    else:
        messages.append({"role": "user", "content": question})

    payload = {
        "model": "mixtral-8x7b-32768",
        "messages": messages,
        "temperature": 0.3,
        "max_tokens": 1024,
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]
