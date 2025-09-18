from flask import Blueprint, jsonify #blueprint is used to group routes
import requests #requests is the HTTP client used to call BB/request GET
import os # 

bp = Blueprint("bulletin", __name__) #creates blueprint

#This reads BB URL from the env
BULLETIN_URL = os.getenv("BULLETIN_URL", "http://localhost:5001")

@bp.get("/bulletin/hello") #define route in VotingApp

#handles the proxy call to BB
def get_hello():
    try:
        r = requests.get(f"{BULLETIN_URL}/hello", timeout=5) #Make GET call to BB /hello endpoint
        r.raise_for_status()
        return jsonify(r.json()) #forwared JSON to front end
    except requests.exceptions.RequestException as e: #catch network errors
        return jsonify({"error": str(e)}), 500 #return an error message
