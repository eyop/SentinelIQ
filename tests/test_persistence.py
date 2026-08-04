from scripts.init_db import Base, CVERecord, AlertRecord


def test_models_can_be_instantiated():
    cve = CVERecord(cve_id="CVE-2024-0001", description="test", severity="HIGH", cvss_score=8.8)
    alert = AlertRecord(source="test", severity="HIGH", message="test", correlated_cves=["CVE-2024-0001"])

    assert cve.cve_id == "CVE-2024-0001"
    assert alert.source == "test"
    assert alert.correlated_cves == ["CVE-2024-0001"]
    assert "cves" in Base.metadata.tables
    assert "alerts" in Base.metadata.tables
