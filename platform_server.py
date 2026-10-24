#!/usr/bin/env python3
"""Same API behavior as the CloudOps microservices, in one process."""

import hashlib
import json
import os
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

DATA = Path(os.environ.get("DATA_DIR", "/var/www/cloudops-monolithic-bookstore/data"))
DATA.mkdir(parents=True, exist_ok=True)
PASS_SALT = os.environ.get("PASS_SALT", "cloudops-academy-demo")

BOOKS = [
    {"id": "aws", "name": "AWS book", "price": 22},
    {"id": "terraform", "name": "Terraform book", "price": 19},
    {"id": "kubernetes", "name": "Kubernetes book", "price": 24},
    {"id": "docker", "name": "Docker book", "price": 16},
    {"id": "ansible", "name": "Ansible book", "price": 17},
    {"id": "github", "name": "GitHub Actions", "price": 18},
    {"id": "jenkins", "name": "Jenkins book", "price": 15},
    {"id": "git", "name": "Git book", "price": 14},
    {"id": "python", "name": "Python book", "price": 20},
    {"id": "linux", "name": "Linux book", "price": 16},
    {"id": "prometheus", "name": "Prometheus book", "price": 21},
    {"id": "grafana", "name": "Grafana book", "price": 21},
    {"id": "otel", "name": "OpenTelemetry", "price": 19},
    {"id": "argo", "name": "Argo CD book", "price": 20},
    {"id": "helm", "name": "Helm book", "price": 18},
    {"id": "istio", "name": "Istio book", "price": 20},
    {"id": "opensearch", "name": "OpenSearch book", "price": 19},
    {"id": "elasticsearch", "name": "Elasticsearch", "price": 19},
    {"id": "kibana", "name": "Kibana book", "price": 18},
    {"id": "mlflow", "name": "MLflow book", "price": 21},
    {"id": "tensorflow", "name": "TensorFlow book", "price": 22},
    {"id": "pytorch", "name": "PyTorch book", "price": 22},
    {"id": "mongodb", "name": "MongoDB book", "price": 18},
    {"id": "postgresql", "name": "PostgreSQL book", "price": 18},
    {"id": "redis", "name": "Redis book", "price": 16},
    {"id": "nginx", "name": "Nginx book", "price": 15},
    {"id": "mlops", "name": "MLOps book", "price": 23},
    {"id": "security", "name": "Security book", "price": 22},
    {"id": "exam", "name": "Exam pack", "price": 25},
]
NAMES = {row["id"]: row["name"] for row in BOOKS}
LABS = [
    {"id": "terraform", "name": "Terraform apply", "note": "Plan a node group change, then apply."},
    {"id": "eks", "name": "EKS rollout", "note": "kubectl get, then rollout status."},
    {"id": "mlops", "name": "MLOps loop", "note": "Train, register, deploy, watch."},
]


def load(name):
    path = DATA / name
    if not path.exists():
        return []
    return json.loads(path.read_text())


def save(name, rows):
    (DATA / name).write_text(json.dumps(rows, indent=2))


def digest(password):
    return hashlib.sha256(f"{PASS_SALT}:{password}".encode()).hexdigest()


def now_stamp():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def signup(payload):
    name = (payload.get("name") or "").strip()
    email = (payload.get("email") or "").strip().lower()
    password = payload.get("password") or ""
    if not name or not email or len(password) < 6:
        return 400, {"message": "Name, email, and a 6+ character password are required."}
    rows = load("users.json")
    if any(user.get("email") == email for user in rows):
        return 409, {"message": "That email already has an account. Login instead."}
    row = {"name": name, "email": email, "password": digest(password)}
    rows.append(row)
    save("users.json", rows)
    return 201, {"name": row["name"], "email": row["email"]}


def login(payload):
    email = (payload.get("email") or "").strip().lower()
    password = payload.get("password") or ""
    hit = next((user for user in load("users.json") if user.get("email") == email and user.get("password") == digest(password)), None)
    if not hit:
        return 401, {"message": "Email or password is wrong."}
    return 200, {"name": hit["name"], "email": hit["email"]}


def get_cart(query):
    email = (query.get("email") or "").strip().lower()
    hit = next((row for row in load("carts.json") if row.get("email") == email), {"email": email, "items": []})
    return 200, hit


def save_cart(payload):
    email = (payload.get("email") or "").strip().lower()
    items = payload.get("items") or []
    if not email:
        return 400, {"message": "Email is required."}
    rows = load("carts.json")
    found = False
    for row in rows:
        if row.get("email") == email:
            row["items"] = items
            found = True
            break
    if not found:
        rows.append({"email": email, "items": items})
    save("carts.json", rows)
    return 200, {"email": email, "items": items}


def issue_certificate(cert):
    certs = load("certificates.json")
    cert = dict(cert)
    cert["id"] = cert.get("id") or f"CERT-{len(certs) + 1:04d}"
    certs.append(cert)
    save("certificates.json", certs)
    return cert


def sit_exam(payload):
    score = int(payload.get("score") or 0)
    book_id = payload.get("book_id") or ""
    passed = score >= 70
    email = (payload.get("email") or "").lower()
    name = (payload.get("name") or "").strip()
    if not name:
        hit = next((user for user in load("users.json") if user.get("email") == email), None)
        name = (hit or {}).get("name") or (email.split("@")[0] if email else "Learner")
    row = {
        "name": name,
        "email": email,
        "book": NAMES.get(book_id, book_id),
        "score": score,
        "passed": passed,
        "when": now_stamp(),
    }
    rows = load("exams.json")
    rows.append(row)
    save("exams.json", rows)
    if passed:
        issued = datetime.now(timezone.utc)
        until = issued + timedelta(days=365)
        row["certificate"] = issue_certificate({
            "name": name,
            "email": row["email"],
            "book": row["book"],
            "score": score,
            "when": issued.strftime("%Y-%m-%d"),
            "valid_until": until.strftime("%Y-%m-%d"),
            "valid_for": "1 year",
            "wish": "All the best for the year ahead.",
        })
    return 200, row


def buy(payload):
    items = payload.get("items") or []
    books = ", ".join(NAMES.get(item.get("id"), item.get("id")) for item in items)
    row = {
        "name": payload.get("name") or "Learner",
        "email": (payload.get("email") or "").lower(),
        "books": books,
        "when": now_stamp(),
    }
    rows = load("orders.json")
    rows.append(row)
    save("orders.json", rows)
    return 201, {"message": f"Purchased: {books}", "order": row}


def post_thread(payload):
    thread = {
        "name": payload.get("name") or "Learner",
        "title": (payload.get("title") or "").strip(),
        "body": (payload.get("body") or "").strip(),
        "when": now_stamp(),
    }
    if not thread["title"] or not thread["body"]:
        return 400, {"message": "Title and question are required."}
    rows = load("threads.json")
    rows.insert(0, thread)
    save("threads.json", rows)
    return 201, thread



def forward_course_marks(payload):
    import urllib.error
    import urllib.request
    env = {}
    config = Path("/var/www/cloudops-monolithic-bookstore/course-marks/course-marks.env")
    if not config.exists():
        return 503, {"ok": False, "message": "Course marks API is not configured."}
    for line in config.read_text().splitlines():
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        env[key] = value
    req = urllib.request.Request(
        env["API_URL"],
        data=json.dumps(payload).encode(),
        method="POST",
        headers={"content-type": "application/json", "x-course-marks-token": env["COURSE_MARKS_TOKEN"]},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as res:
            return res.status, json.loads(res.read().decode() or "{}")
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read().decode() or "{}")


GETS = {
    "/api/books": lambda _query: (200, BOOKS),
    "/api/cart": get_cart,
    "/api/orders": lambda _query: (200, load("orders.json")),
    "/api/exams": lambda _query: (200, load("exams.json")),
    "/api/labs": lambda _query: (200, LABS),
    "/api/community": lambda _query: (200, load("threads.json")),
    "/api/certificates": lambda _query: (200, load("certificates.json")),
    "/api/leaderboard": lambda _query: (200, sorted(load("exams.json"), key=lambda row: (-int(row.get("score") or 0), row.get("when") or ""))[:20]),
}
POSTS = {
    "/api/signup": signup,
    "/api/login": login,
    "/api/cart": save_cart,
    "/api/buy": buy,
    "/api/exam": sit_exam,
    "/api/certificates": lambda payload: (201, issue_certificate(payload)),
    "/api/community": post_thread,
    "/api/course-marks": forward_course_marks,
}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        return

    def _json(self, code, payload):
        body = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        if path in ("/health", "/api/health"):
            return self._json(200, {"ok": True, "service": "monolith"})
        fn = GETS.get(path)
        if not fn:
            return self._json(404, {"message": "Not found", "service": "monolith"})
        query = {key: value[0] for key, value in parse_qs(parsed.query).items()}
        code, payload = fn(query)
        return self._json(code, payload)

    def do_POST(self):
        parsed = urlparse(self.path)
        length = int(self.headers.get("Content-Length") or 0)
        try:
            payload = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            return self._json(400, {"message": "Request body must contain valid JSON."})
        if not isinstance(payload, dict):
            return self._json(400, {"message": "Request body must be a JSON object."})
        fn = POSTS.get(parsed.path)
        if not fn:
            return self._json(404, {"message": "Not found", "service": "monolith"})
        code, body = fn(payload)
        return self._json(code, body)


if __name__ == "__main__":
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8090"))
    print(f"monolith listening on {host}:{port}", flush=True)
    ThreadingHTTPServer((host, port), Handler).serve_forever()
