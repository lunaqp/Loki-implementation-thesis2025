#Has to run along with other api's + web app. To run -> python apiBB.py
from flask import Flask, jsonify
import sys
sys.path.append("..")
from database.queries import *

app = Flask(__name__)

@app.get("/hello") #Defines HTTP Get route at /hello
#a function that runs when client requests /hello
def hello():
    return jsonify({"message": "Hello World from BulletinBoard!"})

@app.get("/bulletin/candidates")
def candidates():
    candidates = fetch_candidates_for_election(0)
    candidates_dict = [{"id": cid, "name": name} for cid, name in candidates]
    print(candidates_dict)

    return jsonify({"candidates": candidates_dict})

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5001, debug=True) #start server listening on 5001. 
    #0.0.0.0 makes it reachable from other processes/machines.
    #127.0.0.1 sets so it only listens to my machine. only processes on my computer can reach /hello
