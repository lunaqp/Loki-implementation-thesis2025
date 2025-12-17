# Loki-implementation-thesis2025

This project is a prototype implementation of the coercion-resistant e-voting scheme Loki as proposed in "Thwarting Last-Minute Voter Coercion" by Rosario Giustolisi, Maryam Sheikhi Garjan, and Carsten Schuermann.

The project is built as two separate Docker compose projects consisting of a number of services.

The "BackendSystems" consists of the following services:
- bb_api (Bulletin Board)
  - A PostgresQL database
  - Adminer for inspecting the PostgreSQL database
- ra_api (Registration Authority)
- vs_api (Voting Server)
- ts_api (Tallying Server)

The "VotingApp" consists of the following services:
- va_api (Voting App backend)
- va_web (Voting App frontend)

The BackendSystems make up the core of the election system and would ideally be hosted on a server, or a computer functioning as the server. The Voting App can be replicated based on the amount of voters participating in an election. All services need to be on the same network and the Voting App needs to be configured with the IP of the server in order to communicate with the rest of the system.

## Requirements
The only prerequisite is an installation of Docker, which manages project dependencies.

## Preparations for running an election: 
A few manual modifications have to be made in order to run an election.

### Network setup
The Voting App needs to be able to communicate with the rest of the system. For this purpose the network needs to be defined in the docker compose environment.

Edit the docker-compose.yml located at /VotingApp/docker-compose-yml. Add the following under "environment", while replacing \<IP\> with your own network.
```
BB_API_URL: http://<IP>:8001
RA_API_URL: http://<IP>:8002
VS_API_URL: http://<IP>:8004
```

### Editing initial ballot amount
In the file at /BackendSystems/VotingServer/epochGeneration.py, the interval of ballots initially allocated to each voter needs to be defined.

For the function "generate_voteamount()" replace the XX values below with a minimum and maximum value:
```
voteamount = generator.integers(low=XX, high=XX, size=None, dtype=np.int64, endpoint=True)
```
For a six-hour election period, we suggest a low of 180 and high of 200. Note that the system cannot support more than at most 256 total ballots per voter. We recommend a "high" value not surpassing 220.\
For shorter election durations, the values should be lowered accordingly.\
The system is designed to support elections of around 40 ballots an hour.

### Preparing election data
Elections are loaded into the system through files located in the directory electiondata (/BackendSystems/RegistrationAuthority/api/electionData/).
New elections can either be added by creating a new JSON-file from scrath with the desired election data (view existing files to see the necessary struture), or by modifying the time and date of one of the existing JSON-files (election1.json, election2.json).

Be mindful of the allocated ballot amount, as this should be increased and decreased to match the election length.

Defining the time and date might require adjustsments depending on local timezone. The project has been tested in Copenhagen wintertime, where it has been necessary to define the election start time in the JSON-file as one hour earlier than the intended start time.

## Scripts for running the project
Two scripts have been added for convenience, for both bash and powershell.

### Run backend systems
One script runs the backend systems (Bulletin Board, Registration Authority, Voting Server and Tallying Server) and is located under /BackendSystems/. Run it with one of the following:

Powershell:
```
run_backendsystems.ps
```
Bash:
```
run_backendsystems.sh
```

From here the script provides different options from 1-4:
1. Load election 1
2. Load election 2
3. Rerun application from scratch
4. Exit (closes and removes Docker images)
Choose an option by typing the number in the terminal.

### Run Voting App backend and frontend
The other script runs the Voting App frontend and backend as is located under /VotingApp.

Run it with the following, replacing <voter_id> with the voter id of a specific voter (voter ids are defined in the JSON-file with the election data):

Powershell:
```
start_va_containers.ps1 <voter_id>
```
Bash:
```
start_va_containers.sh <voter_id>
```

Once the container is running, the frontend can be visited at [localhost port 5173](http://localhost:5173).

To log in with a given user, the default credentials are voter\<id\> and pass\<id\>. The voter with id "3" would log in with credentials:
- username: voter3
- password: pass3

## Colour coding
We have colour-coded the logs for all of the services based on the following:

- Blue: setup functionality running before any elections are received.
- Cyan: initialisation process once election is loaded
- Yellow: obfuscated ballots
- Green: all other ballots
- Purple: end of election and tallying
- Red: errors
- Pink: performance logging
