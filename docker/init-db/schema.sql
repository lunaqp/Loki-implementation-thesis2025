DROP TABLE IF EXISTS Elections CASCADE;
DROP TABLE IF EXISTS Candidates CASCADE;
DROP TABLE IF EXISTS CandidateRunsInElection CASCADE;
DROP TABLE IF EXISTS Voters CASCADE;
DROP TABLE IF EXISTS VoterParticipatesInElection CASCADE;
DROP TABLE IF EXISTS Ballots CASCADE;
DROP TABLE IF EXISTS VoterCastsBallot CASCADE;
DROP TABLE IF EXISTS Images CASCADE;
DROP TABLE IF EXISTS VotingServer CASCADE;
DROP TABLE IF EXISTS GlobalInfo CASCADE;
DROP TYPE IF EXISTS ct_tuple CASCADE;

CREATE TABLE Elections (
    ID INT PRIMARY KEY,
    Name VARCHAR(50) NOT NULL,
    ElectionStart TIMESTAMPTZ NOT NULL,
    ElectionEnd TIMESTAMPTZ NOT NULL
);

CREATE TABLE Candidates (
    ID INT PRIMARY KEY,
    Name VARCHAR(50) NOT NULL
);

CREATE TABLE CandidateRunsInElection (
    CandidateID INT REFERENCES Candidates(ID),
    ElectionID INT REFERENCES Elections(ID),
    PRIMARY KEY (CandidateID, ElectionID),
    RESULT INT
);

CREATE TABLE Voters (
    ID INT PRIMARY KEY,
    Name VARCHAR(50) NOT NULL,
    PublicKey INT
    -- password
);

CREATE TABLE VoterParticipatesInElection (
    ElectionID INT REFERENCES Elections(ID),
    VoterID INT REFERENCES Voters(ID),
    PRIMARY KEY (VoterID, ElectionID),
    PublicKey BYTEA NOT NULL,
    SecretKey BYTEA NOT NULL -- Currently saved encrypted with a symmetric key.
);

CREATE TYPE ct_tuple AS (
    c1 BYTEA, 
    c2 BYTEA
);

CREATE TABLE Ballots (
    ID INT PRIMARY KEY,
    CtCandidate ct_tuple ARRAY NOT NULL,
    CtVoterList ct_tuple NOT NULL,
    CtVotingServerList ct_tuple NOT NULL,
    Valid BOOLEAN NOT NULL
);

CREATE TABLE VoterCastsBallot (
    BallotID INT PRIMARY KEY REFERENCES Ballots(ID),
    VoterID INT REFERENCES Voters(ID),
    ElectionID INT REFERENCES Elections(ID),
    VoteTimestamp TIMESTAMP NOT NULL -- multiple type options - we need to reflect on what fits best.
);

CREATE TABLE Images (
    ImageFilename VARCHAR(20) NOT NULL,
    BallotID INT PRIMARY KEY REFERENCES Ballots(ID)
);

CREATE TABLE VotingServer (
    PublicKey INT NOT NULL,
    PrivateKey INT NOT NULL
    --ct_lid moved into participation relation?
);

CREATE TABLE GlobalInfo ( -- Probably not ints.
    ID INT PRIMARY KEY,
    PublicKeyTallyingServer BYTEA,
    PublicKeyVotingServer BYTEA,
    GroupCurve INT,
    Generator BYTEA,
    OrderP BYTEA
);

INSERT INTO GlobalInfo (ID, PublicKeyTallyingServer, PublicKeyVotingServer, Generator, OrderP) VALUES
    (0, null, null, null, null)

