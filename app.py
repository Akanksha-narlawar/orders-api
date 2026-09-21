from flask import Flask, jsonify
import os

app = Flask(__name__)

VERSION = os.getenv("APP_VERSION", "7.8")
ENVIRONMENT = os.getenv("ENVIRONMENT", "PRODUCTION")

@app.route("/")
def home():
    return jsonify({
        "application": "orders-api",
        "version": VERSION,
        "environment": ENVIRONMENT
    })

@app.route("/health")
def health():
    return jsonify({
        "status": "UP",
        "version": VERSION
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)