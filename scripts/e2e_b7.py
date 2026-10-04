import json, urllib.request, urllib.error, uuid

BASE = "http://127.0.0.1:8001/api/v1"

def req(method, path, token=None, body=None):
    url = BASE + path
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(url, data=data, method=method)
    r.add_header("Content-Type", "application/json")
    if token:
        r.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(r) as resp:
            raw = resp.read().decode()
            return resp.status, (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, raw

def mkuser():
    u = f"b7_{uuid.uuid4().hex[:8]}"
    st, reg = req("POST", "/auth/register", body={"email": f"{u}@example.com", "username": u, "password": "RallyPass123"})
    assert st == 201, (st, reg)
    st, tok = req("POST", "/auth/login", body={"email": f"{u}@example.com", "password": "RallyPass123"})
    assert st == 200, (st, tok)
    return reg["user"]["id"], tok["tokens"]["access_token"]

organizer, org_tok = mkuser()
players = [mkuser() for _ in range(4)]

st, t = req("POST", "/tournaments", token=org_tok, body={
    "name": "Batch7 Live Cup", "description": "E2E", "max_entries": 8})
print("CREATE", st, t["id"], t["status"])
tid = t["id"]

entries = []
for uid, tok in players:
    st, e = req("POST", f"/tournaments/{tid}/register", token=tok)
    print("REGISTER", st, e["id"] if isinstance(e, dict) else e)
    entries.append(e["id"])

st, br = req("POST", f"/tournaments/{tid}/bracket", token=org_tok)
print("BRACKET", st, "rounds=", br["rounds"], "matches=", len(br["matches"]))

rounds = sorted({m["round_number"] for m in br["matches"]})
for rnd in rounds:
    cur = [m for m in req("GET", f"/tournaments/{tid}/bracket")[1]["matches"] if m["round_number"] == rnd]
    for m in cur:
        st, res = req("POST", f"/tournaments/{tid}/results", token=org_tok, body={
            "bracket_match_id": m["id"], "winner_entry_id": m["home_entry_id"],
            "home_score": 3, "away_score": 1})
        print("RESULT", st, "round", rnd, "winner", res.get("winner_entry_id"))

st, s = req("GET", f"/tournaments/{tid}/standings")
print("STANDINGS", st)
print(json.dumps(s["standings"], indent=2))
print("TOURNAMENT STATUS", s["status"])
