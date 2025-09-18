from flask import Blueprint, jsonify
import requests
import os

bp = Blueprint("bulletin", __name__)

BULLETIN_BASE_URL = os.getenv("BULLETIN_BASE_URL", "http://localhost:5001")

@bp.get("/bulletin/hello")
def get_hello():
    try:
        r = requests.get(f"{BULLETIN_BASE_URL}/hello", timeout=5)
        r.raise_for_status()
        return jsonify(r.json())
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500
