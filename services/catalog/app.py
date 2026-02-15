import os
import jwt
import mysql.connector
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)

CORS(app, resources={r"/*": {"origins": "*"}}, allow_headers=["Content-Type", "Authorization"])

# MySQL env (from .env / docker-compose)
MYSQL_HOST = os.getenv("MYSQL_HOST", "mysql")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "data_db")
MYSQL_USER = os.getenv("MYSQL_USER", "appuser")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "apppass")

# JWT (same secret as auth service)
JWT_SECRET = os.getenv("JWT_SECRET", "devsecret")

def get_conn():
    return mysql.connector.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE,
    )

def ensure_table():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS videos (
          id INT AUTO_INCREMENT PRIMARY KEY,
          title VARCHAR(255) NOT NULL,
          path VARCHAR(1024) NOT NULL,
          uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    cur.close()
    conn.close()

def require_jwt():
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
    # verify DB connectivity too
    try:
        conn = get_conn()
        conn.close()
        return {"status": "ok", "db": "ok"}, 200
    except Exception as e:
        return {"status": "error", "db": str(e)}, 500

@app.get("/videos")
def list_videos():
    ensure_table()
    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT id, title, path, uploaded_at FROM videos ORDER BY id DESC;")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(rows), 200

@app.post("/videos")
def create_video():
    if not require_jwt():
        return jsonify({"error": "unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    path = (data.get("path") or "").strip()

    if not title or not path:
        return jsonify({"error": "title and path required"}), 400

    ensure_table()
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO videos (title, path) VALUES (%s, %s);", (title, path))
    conn.commit()
    new_id = cur.lastrowid
    cur.close()
    conn.close()

    return jsonify({"id": new_id, "title": title, "path": path}), 201

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)

