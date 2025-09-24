from flask import Flask, jsonify

app = Flask(__name__)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5002, debug=True) #start server listening on 5001. 
    #0.0.0.0 makes it reachable from other processes/machines.
    #127.0.0.1 sets so it only listens to my machine. only processes on my computer can reach /hello
