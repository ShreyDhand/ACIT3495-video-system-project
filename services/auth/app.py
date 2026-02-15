import os
import datetime
import jwt
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)

CORS(app, resources={r"/*": {"origins": "*"}}, allow_headers=["Content-Type", "Authorization"])

JWT_SECRET = os.getenv("JWT_SECRET", "devsecret")
JWT_ISSUER = os.getenv("JWT_ISSUER", "acit3495")
JWT_TTL_MIN = int(os.getenv("JWT_TTL_MIN", "60"))

# SUPER simple users (good enough for “simple auth service”)
USERS = {
    "demo": "demo123",
    "admin": "admin123",
}

def make_token(username: str) -> str:
    now = datetime.datetime.utcnow()
    payload = {
        "sub": username,
        "iss": JWT_ISSUER,
        "iat": now,
        "exp": now + datetime.timedelta(minutes=JWT_TTL_MIN),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

def extract_bearer_token() -> str | None:
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth.split(" ", 1)[1].strip()
    return None

@app.get("/health")
def health():
    return {"status": "ok"}, 200

@app.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = (data.get("password") or "").strip()

    if not username or not password:
        return jsonify({"error": "username and password required"}), 400

    if USERS.get(username) != password:
        return jsonify({"error": "invalid credentials"}), 401

    token = make_token(username)
    return jsonify({"user": username, "token": token}), 200

@app.post("/verify")
def verify():
    token = extract_bearer_token()
    if not token:
        return jsonify({"valid": False, "error": "missing bearer token"}), 401

    try:
        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=["HS256"],
            issuer=JWT_ISSUER,
            options={"require": ["exp", "iat", "iss", "sub"]},
        )
        return jsonify({"valid": True, "user": payload["sub"]}), 200
    except Exception as e:
        return jsonify({"valid": False, "error": str(e)}), 401

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=4000)

