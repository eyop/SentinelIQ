from fastapi import APIRouter

router = APIRouter(tags=['dashboard'])


@router.get('/alerts')
async def list_alerts() -> list[dict[str, object]]:
    return [
        {'id': 1, 'severity': 'High', 'title': 'Suspicious PowerShell execution', 'source': 'Elastic'},
        {'id': 2, 'severity': 'Medium', 'title': 'Multiple failed SSH logins', 'source': 'SSH'},
        {'id': 3, 'severity': 'Low', 'title': 'New CVE observed in local feed', 'source': 'NVD'}
    ]


@router.get('/cves')
async def list_cves() -> list[dict[str, object]]:
    return [
        {'id': 'CVE-2024-21626', 'severity': 'High', 'summary': 'Container breakout in runc'},
        {'id': 'CVE-2024-3400', 'severity': 'Medium', 'summary': 'Command injection in Palo Alto'},
        {'id': 'CVE-2023-23397', 'severity': 'High', 'summary': 'ZeroLogon privilege escalation'}
    ]
