from flask import Flask, jsonify

app = Flask(__name__)

@app.get("/hello")
def hello():
    return jsonify({"message": "Hello World from BulletinBoard!"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
