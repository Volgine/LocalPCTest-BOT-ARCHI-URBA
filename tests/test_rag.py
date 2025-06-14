import importlib
import sys
import types
import pytest
import asyncio
from pathlib import Path

# Ensure backend package can be imported
BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))


class DummyCollection:
    def __init__(self):
        self.queries = []
    def query(self, query_texts, n_results=5):
        self.queries.append((tuple(query_texts), n_results))
        return {"documents": [["snippet"]]}

class DummyClient:
    def __init__(self, *a, **k):
        self.collection = DummyCollection()
    def get_or_create_collection(self, *a, **k):
        return self.collection

dummy_embedding_functions = types.SimpleNamespace(
    SentenceTransformerEmbeddingFunction=lambda *a, **k: None
)
dummy_chromadb = types.SimpleNamespace(
    PersistentClient=DummyClient,
    utils=types.SimpleNamespace(embedding_functions=dummy_embedding_functions),
)

@pytest.fixture()
def rag(monkeypatch):
    class _DummyAsyncClient:
        def __init__(self, *a, **k):
            pass
        async def __aenter__(self):
            return self
        async def __aexit__(self, exc_type, exc, tb):
            pass
        async def post(self, *a, **k):
            return None

    dummy_httpx = types.SimpleNamespace(AsyncClient=_DummyAsyncClient)
    dummy_dotenv = types.SimpleNamespace(load_dotenv=lambda: None)

    monkeypatch.setitem(sys.modules, 'chromadb', dummy_chromadb)
    monkeypatch.setitem(sys.modules, 'chromadb.utils', dummy_chromadb.utils)
    monkeypatch.setitem(sys.modules, 'httpx', dummy_httpx)
    monkeypatch.setitem(sys.modules, 'dotenv', dummy_dotenv)

    rag_utils = importlib.import_module('backend.rag_utils')
    importlib.reload(rag_utils)
    return rag_utils

def test_retrieve_and_generate(monkeypatch, rag):

    class DummyClient:
        def __init__(self, *a, **k):
            pass
        async def __aenter__(self):
            return self
        async def __aexit__(self, exc_type, exc, tb):
            pass
        async def post(self, url, headers=None, json=None):
            return types.SimpleNamespace(status_code=200,
                                         json=lambda: {'choices': [{'message': {'content': 'Ok'}}]},
                                         raise_for_status=lambda: None)

    monkeypatch.setattr(rag.httpx, 'AsyncClient', DummyClient)
    question = 'Quelle est la hauteur maximale?'
    context = ' '.join(rag.retrieve_context(question))
    answer = asyncio.run(rag.generate_llm_answer(question, context, 'key'))
    assert answer
