from flask import Flask, request, jsonify
import json, os

app = Flask(__name__)

# 🔹 File chứa danh sách key hợp lệ
KEYS_FILE = "keys.json"

# 🔹 Nếu chưa có file keys.json thì tạo mặc định
if not os.path.exists(KEYS_FILE):
    with open(KEYS_FILE, "w") as f:
        json.dump({"valid_keys": ["DUONG123", "VIP2025", "TESTKEY"]}, f, indent=4)

# 🔹 Hàm đọc danh sách key
def load_keys():
    with open(KEYS_FILE, "r") as f:
        return json.load(f)["valid_keys"]

# 🔹 Hàm lưu danh sách key
def save_keys(keys):
    with open(KEYS_FILE, "w") as f:
        json.dump({"valid_keys": keys}, f, indent=4)

# 🔐 Tài khoản admin hợp lệ (bạn có thể thêm nhiều tài khoản ở đây)
ADMINS = {
    "duong2024": "duongpizza",
    "admin": "supersecret123"
}

@app.route("/")
def home():
    return "✅ API Key Server with Admin Login is running!"

# 🔹 Kiểm tra key hợp lệ
@app.route("/verify")
def verify():
    key = request.args.get("key")
    valid_keys = load_keys()
    return jsonify({"valid": key in valid_keys})

# 🔹 API thêm key mới — yêu cầu admin có tài khoản + mật khẩu
@app.route("/add_key")
def add_key():
    username = request.args.get("user")
    password = request.args.get("pass")
    new_key = request.args.get("key")

    # 🛡️ Kiểm tra đăng nhập admin
    if username not in ADMINS or ADMINS[username] != password:
        return jsonify({"error": "Sai tài khoản hoặc mật khẩu admin!"}), 403

    if not new_key:
        return jsonify({"error": "Thiếu key cần thêm!"}), 400

    keys = load_keys()
    if new_key in keys:
        return jsonify({"message": "Key đã tồn tại!"})
    else:
        keys.append(new_key)
        save_keys(keys)
        return jsonify({"success": True, "added": new_key})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
