# server.py
from flask import (
    Flask, request, jsonify, session,
    redirect, url_for, render_template_string, abort
)
from flask_sqlalchemy import SQLAlchemy
import json, os

app = Flask(__name__)

# ===================== SỬA ĐỔI BẢO MẬT =====================
# BẮT BUỘC: Bạn phải đặt biến này trong Environment Variables trên Render
app.secret_key = os.environ.get("APP_SECRET_KEY")
if not app.secret_key:
    # App sẽ không khởi động nếu thiếu key này
    raise ValueError("Chưa đặt APP_SECRET_KEY trong Environment Variables!")

# ===================== SỬA ĐỔI LƯU TRỮ (DATABASE) =====================
# Lấy DATABASE_URL (Render tự động cung cấp qua envVars trong render.yaml)
db_url = os.environ.get('DATABASE_URL')
if not db_url:
    raise ValueError("Chưa đặt DATABASE_URL!")

# Fix lỗi "postgresql://" mà Heroku/Render hay dùng
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Định nghĩa Bảng (Model) để lưu API keys
class ApiKey(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)

    def __repr__(self):
        return f'<ApiKey {self.key}>'

def create_db():
    """Hàm này được gọi bởi render.yaml (buildCommand) để tạo bảng."""
    print("Connecting to DB and creating tables...")
    try:
        with app.app_context():
            db.create_all()
        print("Database tables created successfully (hoặc đã tồn tại).")
    except Exception as e:
        print(f"Lỗi khi tạo database: {e}")
        # Thử tạo key mặc định nếu bảng đã có
        try:
            init_default_keys()
        except Exception as e2:
            print(f"Lỗi khi thêm key mặc định: {e2}")

def init_default_keys():
    """Thêm key mặc định nếu database trống."""
    with app.app_context():
        if ApiKey.query.count() == 0:
            print("Database trống, thêm keys mặc định...")
            default_keys = ["DUONG123", "VIP2025", "TESTKEY"]
            for k in default_keys:
                if not ApiKey.query.filter_by(key=k).first():
                    db.session.add(ApiKey(key=k))
            db.session.commit()
            print("Đã thêm keys mặc định.")

# ADMIN ACCOUNTS
ADMINS = {
    "duong2024": "duongpizza"
}

# -----------------------
# Public API endpoints
# -----------------------
@app.route("/")
def home():
    return "✅ API Key Server (Database) is running!"

@app.route("/verify")
def verify():
    key = request.args.get("key", "")
    if not key:
        return jsonify({"valid": False, "reason": "Không cung cấp API Key."}), 400

    # Tìm key trong database
    key_obj = ApiKey.query.filter_by(key=key).first()
    
    if key_obj:
        return jsonify({"valid": True})
    else:
        return jsonify({"valid": False, "reason": "API Key không hợp lệ hoặc đã hết hạn."}), 401

# -----------------------
# Admin web UI & actions
# (Logic đã được cập nhật để dùng DB)
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

<h3>Danh sách keys hiện có (Lưu trong Database)</h3>
<ul>
  {% for k in keys %}
    <li>{{ k }}</li>
  {% endfor %}
</ul>
"""

@app.route("/admin")
def admin_index():
    if session.get("admin_user"):
        # Lấy keys từ DB
        keys_obj = ApiKey.query.order_by(ApiKey.key).all()
        keys_list = [k.key for k in keys_obj]
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
    
    # Kiểm tra xem key đã tồn tại chưa
    existing_key = ApiKey.query.filter_by(key=new_key_str).first()
    if not existing_key:
        # Thêm key mới vào DB
        new_key_obj = ApiKey(key=new_key_str)
        db.session.add(new_key_obj)
        db.session.commit()
        
    return redirect(url_for("admin_index"))

@app.route("/admin/remove_key", methods=["POST"])
def admin_remove_key():
    if "admin_user" not in session:
        abort(403)
    key_to_remove_str = request.form.get("key", "").strip()
    
    # Tìm key trong DB
    key_obj = ApiKey.query.filter_by(key=key_to_remove_str).first()
    if key_obj:
        # Xóa key
        db.session.delete(key_obj)
        db.session.commit()
        
    return redirect(url_for("admin_index"))

# (Các endpoint /add_key và /remove_key cũ đã bị xóa để tăng bảo mật,
# chỉ nên dùng giao diện /admin)

# -----------------------
# Run
# -----------------------
if __name__ == "__main__":
    # Thử tạo DB và keys mặc định khi chạy local
    if not os.environ.get("RENDER"):
        with app.app_context():
            db.create_all()
            init_default_keys()
        
    port = int(os.environ.get("PORT", 5000))
    # Dùng host="0.0.0.0" để Render truy cập được
    app.run(host="0.0.0.0", port=port)

