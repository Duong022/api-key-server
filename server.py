from flask import Flask, request, jsonify

app = Flask(__name__)

VALID_KEYS = {"DUONG123", "VIP2025", "TESTKEY"}

@app.route("/")
def home():
    return "✅ API Key Server is running!"

@app.route("/verify")
def verify():
    key = request.args.get("key")
    return jsonify({"valid": key in VALID_KEYS})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
