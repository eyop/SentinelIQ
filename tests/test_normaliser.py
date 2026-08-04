from ingestion.normaliser import cve_to_document, technique_to_document


def test_cve_to_document_normalises_basic_fields():
    raw = {
        "id": "CVE-2024-0001",
        "source": "nvd",
        "description": "A buffer overflow in the service",
        "cvss_score": 8.8,
        "severity": "HIGH",
        "published": "2024-01-01T00:00:00.000",
        "modified": "2024-02-01T00:00:00.000",
        "affected_products": ["Vendor Product"],
        "references": ["https://example.com/advisory"],
        "text": "CVE-2024-0001 buffer overflow",
    }

    doc = cve_to_document(raw)

    assert doc["id"] == "CVE-2024-0001"
    assert doc["severity"] == "HIGH"
    assert doc["doc_type"] == "cve"
    assert "buffer overflow" in doc["text"]


def test_technique_to_document_normalises_basic_fields():
    raw = {
        "id": "T1059",
        "name": "Command and Scripting Interpreter",
        "tactic": "Execution",
        "description": "Adversaries may abuse interpreters",
        "platforms": ["windows", "linux"],
        "mitigations": ["Restrict PowerShell"],
    }

    doc = technique_to_document(raw)

    assert doc["id"] == "T1059"
    assert doc["doc_type"] == "technique"
    assert "Execution" in doc["text"]
    assert "windows" in doc["metadata"]["platforms"]
