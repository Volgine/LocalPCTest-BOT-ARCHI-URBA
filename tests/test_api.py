import json
from fastapi.testclient import TestClient
import backend.main as main

client = TestClient(main.app)

def test_query_returns_answer(monkeypatch):
    def fake_llm(question: str, commune=None):
        return "LLM response"

    monkeypatch.setattr(main, "generate_llm_response", fake_llm)
    response = client.post("/api/query", json={"question": "Test?", "commune": "X"})
    assert response.status_code == 200
    data = response.json()
    assert data["answer"] == "LLM response"
    assert data["answer"]

