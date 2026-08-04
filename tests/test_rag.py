from rag.chunker import chunk_documents
from rag.vectorstore import similarity_search, upsert_documents


def test_chunk_documents_splits_text_and_preserves_metadata():
    docs = [
        {
            "id": "CVE-2024-0001",
            "text": "A long document about a vulnerability that should be split into multiple chunks for retrieval.",
            "metadata": {"source": "nvd", "severity": "HIGH"},
        }
    ]

    chunks = chunk_documents(docs, chunk_size=20, overlap=5)

    assert len(chunks) >= 2
    assert chunks[0]["metadata"]["source"] == "nvd"
    assert chunks[0]["metadata"]["doc_id"] == "CVE-2024-0001"


def test_similarity_search_returns_relevant_chunks():
    documents = [
        {
            "id": "chunk-1",
            "text": "Buffer overflow in the file parser",
            "metadata": {"source": "nvd", "id": "CVE-1"},
        },
        {
            "id": "chunk-2",
            "text": "SQL injection in the login endpoint",
            "metadata": {"source": "nvd", "id": "CVE-2"},
        },
    ]

    upsert_documents(documents)
    results = similarity_search("buffer overflow parser", k=1)

    assert len(results) == 1
    assert "buffer" in results[0]["text"].lower()
