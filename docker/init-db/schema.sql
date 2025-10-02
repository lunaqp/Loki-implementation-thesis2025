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
    ElectionStart DATE NOT NULL,
    ElectionEnd DATE NOT NULL
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
    PublicKey TEXT NOT NULL, -- What type should the keys be stored as? BYTEA?
    SecretKey BYTEA NOT NULL -- Type? + Security considerations for storing this data?
);

CREATE TYPE ct_tuple AS (
    c1 NUMERIC, -- what type to use? Numeric/BYTEA/BIGINT instead of int?
    c2 NUMERIC
);

CREATE TABLE Ballots (
    ID INT PRIMARY KEY,
    CtCandidate ct_tuple NOT NULL,
    CtVoterList ct_tuple NOT NULL,
    CtVotingServerList ct_tuple NOT NULL, -- Should not be stored here - sensitive information.
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
    PublicKeyTallier BYTEA,
    PublicKeyVotingServer BYTEA,
    GroupCurve INT,
    Generator BYTEA,
    OrderP BYTEA
);

INSERT INTO GlobalInfo (ID, PublicKeyTallier, PublicKeyVotingServer, Generator, OrderP) VALUES
    (0, null, null, null, null)

