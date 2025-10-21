# server.py
from flask import (
    Flask, request, jsonify, session,
    redirect, url_for, render_template_string, abort
)
import json, os

app = Flask(__name__)
# ⚠️ Thay đổi giá trị này thành một chuỗi ngẫu nhiên dài (bí mật)
app.secret_key = os.environ.get("APP_SECRET_KEY", "replace_this_with_a_random_secret")

KEYS_FILE = "keys.json"

# Mặc định tạo file keys.json nếu chưa có
if not os.path.exists(KEYS_FILE):
    with open(KEYS_FILE, "w") as f:
        json.dump({"valid_keys": ["DUONG123", "VIP2025", "TESTKEY"]}, f, indent=4)

def load_keys():
    with open(KEYS_FILE, "r") as f:
        return json.load(f)["valid_keys"]

def save_keys(keys):
    with open(KEYS_FILE, "w") as f:
        json.dump({"valid_keys": keys}, f, indent=4)

# ADMIN ACCOUNTS: username -> password (plain text here for simplicity).
# ⚠️ Vì bảo mật, bạn nên đổi mật khẩu và/hoặc lưu hash (mình có hướng dẫn nếu cần).
ADMINS = {
    "duong2024": "duongpizza"
}

# -----------------------
# Public API endpoints
# -----------------------
@app.route("/")
def home():
    return "✅ API Key Server is running!"

@app.route("/verify")
def verify():
    key = request.args.get("key", "")
    keys = load_keys()
    return jsonify({"valid": key in keys})

# -----------------------
# Admin web UI & actions
# -----------------------

# Simple HTML templates (render_template_string used to avoid separate files)
LOGIN_HTML = """
<!doctype html>
<title>Admin Login</title>
<h2>Admin Login</h2>
{% if error %}<p style="color:red;">{{ error }}</p>{% endif %}
<form method="post" action="{{ url_for('admin_login') }}">
  <label>Username: <input name="username"></label><br><br>
  <label>Password: <input name="password" type="password"></label><br><br>
  <button type="submit">Login</button>
</form>
"""

DASHBOARD_HTML = """
<!doctype html>
<title>Admin Dashboard</title>
<h2>Admin Dashboard</h2>
<p>Xin chào, <strong>{{ user }}</strong> — <a href="{{ url_for('admin_logout') }}">Logout</a></p>

<h3>Thêm key mới</h3>
<form method="post" action="{{ url_for('admin_add_key') }}">
  <input name="key" placeholder="NEWKEY2025">
  <button type="submit">Add Key</button>
</form>

<h3>Xóa key</h3>
<form method="post" action="{{ url_for('admin_remove_key') }}">
  <select name="key">
    {% for k in keys %}
      <option value="{{k}}">{{k}}</option>
    {% endfor %}
  </select>
  <button type="submit">Remove Key</button>
</form>

<h3>Danh sách keys hiện có</h3>
<ul>
  {% for k in keys %}
    <li>{{ k }}</li>
  {% endfor %}
</ul>
"""

# Admin landing - show login or dashboard depending on session
@app.route("/admin")
def admin_index():
    if session.get("admin_user"):
        keys = load_keys()
        return render_template_string(DASHBOARD_HTML, user=session["admin_user"], keys=keys)
    else:
        return render_template_string(LOGIN_HTML, error=None)

# Process login
@app.route("/admin/login", methods=["POST"])
def admin_login():
    username = request.form.get("username", "")
    password = request.form.get("password", "")

    if username in ADMINS and ADMINS[username] == password:
        session["admin_user"] = username
        return redirect(url_for("admin_index"))
    else:
        return render_template_string(LOGIN_HTML, error="Sai username hoặc password")

# Logout
@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_user", None)
    return redirect(url_for("admin_index"))

# Add key (from dashboard form)
@app.route("/admin/add_key", methods=["POST"])
def admin_add_key():
    if "admin_user" not in session:
        abort(403)
    new_key = request.form.get("key", "").strip()
    if not new_key:
        return redirect(url_for("admin_index"))
    keys = load_keys()
    if new_key in keys:
        # simple message: redirect (could show message; keeping simple)
        return redirect(url_for("admin_index"))
    keys.append(new_key)
    save_keys(keys)
    return redirect(url_for("admin_index"))

# Remove key (from dashboard form)
@app.route("/admin/remove_key", methods=["POST"])
def admin_remove_key():
    if "admin_user" not in session:
        abort(403)
    key = request.form.get("key", "").strip()
    keys = load_keys()
    if key in keys:
        keys.remove(key)
        save_keys(keys)
    return redirect(url_for("admin_index"))

# Optional programmatic endpoints (still available, protected by credentials)
# Add key via GET/POST using credentials query (backwards-compatible)
@app.route("/add_key")
def add_key_quick():
    user = request.args.get("user")
    passwd = request.args.get("pass")
    new_key = request.args.get("key")
    if not (user and passwd and new_key):
        return jsonify({"error": "Missing parameters"}), 400
    if user not in ADMINS or ADMINS[user] != passwd:
        return jsonify({"error": "Unauthorized"}), 403
    keys = load_keys()
    if new_key in keys:
        return jsonify({"message": "Key already exists"})
    keys.append(new_key)
    save_keys(keys)
    return jsonify({"success": True, "added": new_key})

# Remove key via query (protected)
@app.route("/remove_key")
def remove_key_quick():
    user = request.args.get("user")
    passwd = request.args.get("pass")
    key = request.args.get("key")
    if not (user and passwd and key):
        return jsonify({"error": "Missing parameters"}), 400
    if user not in ADMINS or ADMINS[user] != passwd:
        return jsonify({"error": "Unauthorized"}), 403
    keys = load_keys()
    if key in keys:
        keys.remove(key)
        save_keys(keys)
        return jsonify({"success": True, "removed": key})
    else:
        return jsonify({"message": "Key not found"}), 404

# -----------------------
# Run
# -----------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
