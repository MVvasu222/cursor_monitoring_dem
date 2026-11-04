import os
import secrets

from dotenv import load_dotenv
from flask import Flask, abort, jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash

import metrics
import servers

SIGN_IN_ERROR = "Sign-in failed."


def create_app(*, load_env=True):
    if load_env:
        load_dotenv()

    username = os.environ.get("ADMIN_USERNAME", "")
    password_hash = os.environ.get("ADMIN_PASSWORD_HASH", "")
    secret = os.environ.get("FLASK_SECRET_KEY", "")
    if not username or not password_hash or not secret:
        raise RuntimeError("Set ADMIN_USERNAME, ADMIN_PASSWORD_HASH, and FLASK_SECRET_KEY in .env.")

    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=secret,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=False,
    )
    app.add_template_filter(format_bytes, name="bytes")
    app.add_template_filter(format_timestamp, name="timestamp")

    @app.before_request
    def require_login():
        if request.endpoint in (None, "static", "login"):
            return None
        if session.get("user") != username:
            return redirect(url_for("login"))
        return None

    @app.context_processor
    def inject_csrf():
        return {"csrf_token": session.get("csrf_token", "")}

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if session.get("user") == username and request.method == "GET":
            return redirect(url_for("dashboard"))
        if request.method == "GET":
            return render_template("login.html", error=None)

        given_user = request.form.get("username", "")
        given_password = request.form.get("password", "")
        user_ok = given_user == username
        password_ok = check_password_hash(password_hash, given_password)
        if not (user_ok and password_ok):
            return render_template("login.html", error=SIGN_IN_ERROR)
        session.clear()
        session["user"] = username
        session["csrf_token"] = secrets.token_urlsafe(32)
        return redirect(url_for("dashboard"))

    @app.post("/logout")
    def logout():
        if not _csrf_ok():
            abort(400)
        session.clear()
        return redirect(url_for("login"))

    @app.get("/")
    def dashboard():
        saved = servers.list_servers()
        server = saved[0] if saved else None
        payload = metrics.record_sample()
        return render_template(
            "dashboard.html",
            server=server,
            payload=payload,
            summary=_summary(payload.get("sample")),
        )

    @app.get("/servers")
    def server_list():
        return render_template("servers.html", servers=servers.list_servers(), error=None)

    @app.get("/history")
    def history():
        payload = metrics.record_sample()
        return render_template("history.html", points=list(reversed(payload["history"])))

    @app.post("/servers")
    def add_server():
        if not _csrf_ok():
            abort(400)
        try:
            servers.add_server(request.form.get("name", ""), request.form.get("host", ""))
        except servers.StoreError as exc:
            return render_template("servers.html", servers=servers.list_servers(), error=str(exc)), 400
        return redirect(url_for("server_list"))

    @app.post("/servers/<server_id>/delete")
    def delete_server(server_id):
        if not _csrf_ok() or request.form.get("confirm") != "yes":
            abort(400)
        try:
            servers.remove_server(server_id)
        except servers.StoreError:
            abort(404)
        return redirect(url_for("server_list"))

    @app.get("/servers/<server_id>")
    def server_detail(server_id):
        server = servers.find_server(server_id)
        if server is None:
            abort(404)
        return render_template("detail.html", server=server, payload=metrics.record_sample())

    @app.get("/servers/<server_id>/sample")
    def server_sample(server_id):
        if servers.find_server(server_id) is None:
            abort(404)
        response = jsonify(metrics.record_sample())
        response.headers["Cache-Control"] = "no-store"
        return response

    return app


def _summary(sample):
    if not sample:
        return None
    root = next((disk["percent"] for disk in sample["disks"] if disk["mount"] == "/"), None)
    return {
        "cpu": sample["cpu_percent"],
        "memory": sample["memory"]["percent"],
        "disk": root,
    }


def format_timestamp(value):
    from datetime import datetime

    return datetime.fromtimestamp(value).strftime("%H:%M:%S")


def format_bytes(value):
    size = float(value)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024 or unit == "TB":
            if unit == "B":
                return f"{int(size)} B"
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def _csrf_ok():
    sent = request.form.get("csrf_token", "")
    saved = session.get("csrf_token", "")
    return bool(saved) and secrets.compare_digest(sent, saved)


if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=5000)
