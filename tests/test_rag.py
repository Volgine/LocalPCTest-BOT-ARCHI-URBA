import importlib
import sys
import types
import pytest
import asyncio
from pathlib import Path

# Ensure backend package can be imported
BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

class DummyArray(list):
    def astype(self, dtype):
        return self

class DummySentenceTransformer:
    def __init__(self, name=None):
        self.dim = 3
    def get_sentence_embedding_dimension(self):
        return self.dim
    def encode(self, texts):
        if isinstance(texts, str):
            texts = [texts]
        result = []
        for i, _ in enumerate(texts):
            result.append([float(i + j) for j in range(self.dim)])
        return DummyArray(result)

class DummyFaissIndex:
    def __init__(self, dim):
        self.dim = dim
        self.vectors = []
    def add(self, vectors):
        for vec in vectors:
            self.vectors.append(list(map(float, vec)))
    @property
    def ntotal(self):
        return len(self.vectors)
    def search(self, vector, k):
        dists = []
        for vec in self.vectors:
            dist = sum((v - q) ** 2 for v, q in zip(vec, vector[0]))
            dists.append(dist)
        idx = list(range(len(dists)))
        idx.sort(key=lambda i: dists[i])
        idx = idx[:k]
        return [[dists[i] for i in idx]], [idx]

def dummy_write_index(index, path):
    pass

def dummy_read_index(path):
    return DummyFaissIndex(3)

@pytest.fixture()
def rag(monkeypatch, tmp_path):
    dummy_sentence_module = types.SimpleNamespace(SentenceTransformer=DummySentenceTransformer)
    dummy_faiss_module = types.SimpleNamespace(IndexFlatL2=DummyFaissIndex,
                                               write_index=dummy_write_index,
                                               read_index=dummy_read_index)
    dummy_pypdf2 = types.SimpleNamespace(PdfReader=lambda f: None)
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

    monkeypatch.setitem(sys.modules, 'sentence_transformers', dummy_sentence_module)
    monkeypatch.setitem(sys.modules, 'faiss', dummy_faiss_module)
    monkeypatch.setitem(sys.modules, 'PyPDF2', dummy_pypdf2)
    monkeypatch.setitem(sys.modules, 'httpx', dummy_httpx)
    monkeypatch.setitem(sys.modules, 'dotenv', dummy_dotenv)

    rag_utils = importlib.import_module('backend.rag_utils')
    importlib.reload(rag_utils)
    rag_utils.INDEX_PATH = tmp_path / 'faiss.index'
    rag_utils.DOCS_PATH = tmp_path / 'faiss_docs.json'
    return rag_utils

def test_retrieve_and_generate(monkeypatch, rag, tmp_path):
    doc = tmp_path / 'doc.txt'
    doc.write_text('La hauteur maximale autorisee est de 12 metres.')
    rag.ingest_documents(str(doc))

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
