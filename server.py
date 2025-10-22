# server.py
from flask import (
    Flask, request, jsonify, session,
    redirect, url_for, render_template_string, abort
)
import json, os

app = Flask(__name__)

# ===================== SỬA ĐỔI BẢO MẬT =====================
# BẮT BUỘC: Bạn vẫn phải đặt biến này trong Environment Variables trên Render
app.secret_key = os.environ.get("APP_SECRET_KEY")
if not app.secret_key:
    # App sẽ không khởi động nếu thiếu key này
    raise ValueError("Chưa đặt APP_SECRET_KEY trong Environment Variables!")

# ===================== SỬA ĐỔI LƯU TRỮ =====================
# Thay vì file hay DB, chúng ta dùng một TẬP HỢP (set) trong bộ nhớ.
# Khi server restart, danh sách này sẽ được reset về mặc định.
VALID_KEYS = {
    "DUONG123",
    "VIP2025",
    "TESTKEY"
}

# ADMIN ACCOUNTS
ADMINS = {
    "duong2024": "duongpizza"
}

# -----------------------
# Public API endpoints
# -----------------------
@app.route("/")
def home():
    return "✅ API Key Server (In-Memory) is running!"

@app.route("/verify")
def verify():
    key = request.args.get("key", "")
    if not key:
        return jsonify({"valid": False, "reason": "Không cung cấp API Key."}), 400

    # Kiểm tra key có trong TẬP HỢP (set) không
    if key in VALID_KEYS:
        return jsonify({"valid": True})
    else:
        return jsonify({"valid": False, "reason": "API Key không hợp lệ hoặc đã hết hạn."}), 401

# -----------------------
# Admin web UI & actions
# (Logic đã được cập nhật để dùng bộ nhớ)
# -----------------------

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
  <button type: "submit">Remove Key</button>
</form>

<h3>Danh sách keys hiện có (Lưu trong bộ nhớ)</h3>
<ul>
  {% for k in keys %}
    <li>{{ k }}</li>
  {% endfor %}
</ul>
"""

@app.route("/admin")
def admin_index():
    if session.get("admin_user"):
        # Lấy keys từ bộ nhớ
        keys_list = sorted(list(VALID_KEYS))
        return render_template_string(DASHBOARD_HTML, user=session["admin_user"], keys=keys_list)
    else:
        return render_template_string(LOGIN_HTML, error=None)

@app.route("/admin/login", methods=["POST"])
def admin_login():
    username = request.form.get("username", "")
    password = request.form.get("password", "")

    if username in ADMINS and ADMINS[username] == password:
        session["admin_user"] = username
        return redirect(url_for("admin_index"))
    else:
        return render_template_string(LOGIN_HTML, error="Sai username hoặc password")

@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_user", None)
    return redirect(url_for("admin_index"))

@app.route("/admin/add_key", methods=["POST"])
def admin_add_key():
    if "admin_user" not in session:
        abort(403)
    new_key_str = request.form.get("key", "").strip()
    if not new_key_str:
        return redirect(url_for("admin_index"))
    
    # Thêm key vào TẬP HỢP (set) trong bộ nhớ
    VALID_KEYS.add(new_key_str)
        
    return redirect(url_for("admin_index"))

@app.route("/admin/remove_key", methods=["POST"])
def admin_remove_key():
    if "admin_user" not in session:
        abort(403)
    key_to_remove_str = request.form.get("key", "").strip()
    
    # Xóa key khỏi TẬP HỢP (set) trong bộ nhớ
    if key_to_remove_str in VALID_KEYS:
        VALID_KEYS.remove(key_to_remove_str)
        
    return redirect(url_for("admin_index"))

# -----------------------
# Run
# -----------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    # Dùng host="0.0.0.0" để Render truy cập được
    app.run(host="0.0.0.0", port=port)

