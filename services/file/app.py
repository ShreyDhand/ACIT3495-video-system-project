import os
from flask import Flask, request, jsonify, send_from_directory
import jwt
from flask_cors import CORS


app = Flask(__name__)

CORS(app, resources={r"/*": {"origins": "*"}}, allow_headers=["Content-Type", "Authorization"])

UPLOAD_DIR = "/data"
JWT_SECRET = os.getenv("JWT_SECRET", "devsecret")

os.makedirs(UPLOAD_DIR, exist_ok=True)

def verify_token():
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return False
    token = auth.split(" ", 1)[1].strip()
    try:
        jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return True
    except:
        return False

@app.get("/health")
def health():
    return {"status": "ok"}, 200

@app.post("/upload")
def upload():
    if not verify_token():
        return jsonify({"error": "unauthorized"}), 401

    if "file" not in request.files:
        return jsonify({"error": "no file provided"}), 400

    file = request.files["file"]
    filename = file.filename

    save_path = os.path.join(UPLOAD_DIR, filename)
    file.save(save_path)

    return jsonify({"path": f"/files/{filename}"}), 200

@app.get("/files/<path:filename>")
def serve_file(filename):
    return send_from_directory(UPLOAD_DIR, filename)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
