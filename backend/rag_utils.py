from typing import List

import httpx
from dotenv import load_dotenv

import chromadb
from chromadb.utils import embedding_functions

load_dotenv()

MODEL_NAME = "all-MiniLM-L6-v2"

# ChromaDB collection (shared with main.py)

chroma_client = None
_collection = None


def get_collection():
    """Lazily initialize and return the ChromaDB collection."""
    global chroma_client, _collection
    if _collection is None:
        chroma_client = chromadb.PersistentClient(path="./chroma_db")
        embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=MODEL_NAME
        )
        _collection = chroma_client.get_or_create_collection(
            name="urbanisme_docs",
            embedding_function=embedding_function,
        )
    return _collection







def retrieve_context(question: str, top_k: int = 5) -> List[str]:
    """Return the most relevant snippets for a question using ChromaDB."""
    try:
        col = get_collection()
        results = col.query(query_texts=[question], n_results=top_k)
        return results.get("documents", [[]])[0]
    except Exception:
        return []


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
