# Loki-implementation-thesis2025

A prototype implementation the coercion-resistant e-voting scheme Loki as proposed in "Thwarting Last-Minute Voter Coercion" by Rosario Giustolisi, Maryam Sheikhi Garjan, and Carsten Schuermann.

This project has been created using Python version XX and Node version 22.

How to setup:

1. git clone
2. Open in VS code
3. Create virtual environments in all api folders.

To create venv example:

- In terminal go to BulletinBoard/api
- run "python -m venv venv"
- run "venv\Scripts\activate (windows)
- run "pip install flask python-dotenv"
- run "pip install requests"
  Do the same and create venv for every api folder.

4. Create ".env" file in the api folder and paste in, example:
   "FLASK_APP=apiXX.py
   FLASK_ENV=development"

   Replace XX with initials of the subsystem (e.g. VA/RA/BB etc.)

5. In VotingApp you also need to install npm.

   - Navigate to VotingApp folder in terminal
   - run "npm install"

6. In BulletinBoard we also need to install psycopg for the database.
   Activate the virtual environment and run:
   - pip install "psycopg[binary]"

How to run the app:
run all api's

1. Open a terminal navigate to BulletinBoard/api
   - run "python apiBB.py"
2. Open another terminal, navigate to VotingApp
   - run "npm run api"
3. Open a third terminal, navigate to VotingApp
   - run "npm run dev" + follow link

Setting up database for the Bulletin Board:

1. Install postgres locally.
2. Enter postgres environment:
   - psql -U postgres
3. Create database named "BB":
   - create database BB;
4. Create user for the database:
   - create user bb with encrypted password 'BBpass';
5. Give created user ownership of the database:
   - ALTER DATABASE bb OWNER TO bb;
