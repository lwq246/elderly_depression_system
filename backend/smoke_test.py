import httpx

base = "http://127.0.0.1:8000"
print("health", httpx.get(f"{base}/api/health").json())
s = httpx.post(f"{base}/api/sessions/entry", json={"resident_id": "R-001"}).json()
sid = s["id"]
print("entry", sid, s["transcript"][0]["text"][:50])
s2 = httpx.post(f"{base}/api/sessions/{sid}/message", json={"text": "Yes, can talk."}).json()
print("message turns", len(s2["transcript"]))
s3 = httpx.post(f"{base}/api/sessions/{sid}/exit").json()
print("exit report", s3["report"]["recommendation"] if s3["report"] else None)
print("validation errors", s3["validation_errors"])
