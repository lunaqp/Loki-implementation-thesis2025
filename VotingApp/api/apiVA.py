import time
from flask import Flask
from bulletin_routes import bp as bulletin_bp


app = Flask(__name__)

app.register_blueprint(bulletin_bp, url_prefix="/api")

@app.route('/api/time')
def get_current_time():
    return {'time': time.time()}

@app.route('/api/election')
def get_electionId():
    return {'electionId': 123}

@app.route('/api/elections')
def get_elections():
    return {'electionNo': 2,
            'elections': [
                {'electionId': 0,
                 'electionName': 'Student Council President', 'Candidates': ['Eric', 'Jenna', 'Thomas', 'Cindy']},
                                 {'electionId': 1,
                 'electionName': 'Student Council Treasurer'},
            ]}