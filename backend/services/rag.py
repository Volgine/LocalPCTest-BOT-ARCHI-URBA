import os
from typing import Optional
from dotenv import load_dotenv

from langchain.chains import RetrievalQA
from langchain.embeddings import OpenAIEmbeddings
from langchain.llms import OpenAI, Ollama
from langchain.chat_models import ChatOpenAI
from langchain.vectorstores import FAISS

load_dotenv()

_PIPELINE: Optional[RetrievalQA] = None


def _get_llm() -> object:
    provider = os.getenv("LLM_PROVIDER", "openai").lower()
    model = os.getenv("LLM_MODEL", "")

    if provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not set")
        return OpenAI(openai_api_key=api_key, model_name=model or None, temperature=0)

    if provider == "ollama":
        return Ollama(model=model or "llama2")

    if provider in {"lmstudio", "lm_studio"}:
        base_url = os.getenv("LM_STUDIO_BASE_URL", "http://localhost:1234/v1")
        api_key = os.getenv("LM_STUDIO_API_KEY", "lm-studio")
        return ChatOpenAI(openai_api_base=base_url, openai_api_key=api_key, model=model or None, temperature=0)

    raise ValueError(f"Unsupported LLM_PROVIDER: {provider}")


def build_rag_pipeline() -> RetrievalQA:
    """Create and return a RetrievalQA chain using the configured provider."""
    global _PIPELINE
    if _PIPELINE:
        return _PIPELINE

    embeddings_key = os.getenv("OPENAI_API_KEY")
    if not embeddings_key:
        raise ValueError("OPENAI_API_KEY not set for embeddings")

    embeddings = OpenAIEmbeddings(openai_api_key=embeddings_key)
    store_path = os.getenv("VECTOR_STORE_PATH", "vector_store")

    if not os.path.exists(store_path):
        raise FileNotFoundError(f"Vector store not found at {store_path}")

    vector_store = FAISS.load_local(store_path, embeddings)
    retriever = vector_store.as_retriever(search_kwargs={"k": 4})
    llm = _get_llm()

    _PIPELINE = RetrievalQA.from_chain_type(llm, chain_type="stuff", retriever=retriever)
    return _PIPELINE
