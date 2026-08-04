from rag.vectorstore import upsert_documents
from rag.chain import answer_query


def test_answer_query_fallback_uses_vectorstore():
    docs = [
        {"id": "CVE-1", "text": "Buffer overflow in parser leads to memory corruption", "metadata": {"id": "CVE-1", "source": "nvd"}},
        {"id": "CVE-2", "text": "SQL injection in login endpoint allows data exfiltration", "metadata": {"id": "CVE-2", "source": "nvd"}},
    ]

    upsert_documents(docs)
    res = answer_query("buffer overflow in parser", k=2)

    assert isinstance(res, dict)
    assert res["retrieved_count"] >= 1
    assert "answer" in res
    assert isinstance(res["sources"], list)
