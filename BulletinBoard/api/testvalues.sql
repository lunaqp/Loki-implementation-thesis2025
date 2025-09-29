

INSERT INTO Elections (ID, Name, ElectionStart, ElectionEnd)
VALUES
    (0, 'Student Council President', '2025-09-01', '2025-09-10'),
    (1, 'Student Council Treasurer', '2025-09-01', '2025-09-10');

INSERT INTO Candidates (ID, Name)
VALUES
    (0, 'Snow White'),
    (1, 'Cindarella'),
    (2, 'Superman'),
    (3, 'Magneto');

INSERT INTO CandidateRunsInElection (CandidateID, ElectionID)
VALUES
    (0, 0),
    (1, 0),
    (0, 1),
    (3, 0);

INSERT INTO Voters (ID, Name)
VALUES
    (0, 'Jenna'),
    (1, 'Mike'),
    (2, 'Thomas'),
    (3, 'Sophie');
    -- (4, 'Charlotte'),
    -- (5, 'Stephen'),
    -- (6, 'Max');

-- INSERT INTO Ballots (ID, CtCandidate, CtVoterList, CtVotingServerList, Valid)
-- VALUES
--     (0, (01,01), (02,02), (03,03), TRUE),
    -- (1, (01,01), (02,02), (03,03), TRUE),
    -- (2, (01,01), (02,02), (03,03), TRUE),
    -- (3, (01,01), (02,02), (03,03), TRUE),
    -- (4, (01,01), (02,02), (03,03), TRUE),
    -- (5, (01,01), (02,02), (03,03), TRUE),
    -- (6, (01,01), (02,02), (03,03), TRUE),
    -- (7, (01,01), (02,02), (03,03), TRUE),
    -- (8, (01,01), (02,02), (03,03), TRUE);


-- INSERT INTO VoterParticipatesInElection (VoterID, ElectionID, PublicKey, SecretKey)
-- VALUES
    -- (0, 0, 000, 00000),
    -- (1, 0, 111, 11111),
    -- (2, 0, 222, 22222),
    -- (3, 1, 333, 33333),
    -- (4, 0, 444, 44444),
    -- (5, 0, 555, 55555),
    -- (6, 0, 666, 66666);

-- INSERT INTO VoterCastsBallot (BallotID, VoterID, ElectionID, VoteTimestamp)
-- VALUES
--     (0, 0, 0, '2025-09-18 00:00:00'),
--     (1, 1, 0, '2025-09-18 00:00:01'),
--     (2, 2, 0, '2025-09-18 00:00:02'),
--     (3, 3, 1, '2025-09-18 00:00:03');
    -- (4, 4, 0, '2025-09-18 00:00:04'),
    -- (5, 5, 0, '2025-09-18 00:00:05'),
    -- (6, 2, 0, '2025-09-18 00:00:06'),
    -- (7, 2, 0, '2025-09-18 00:00:07');

-- INSERT INTO Images (BallotID, ImageFilename)
-- VALUES
--     (0, 'File 0'),
--     (1, 'File 1'),
--     (2, 'File 2'),
--     (3, 'File 3'),
--     (4, 'File 4'),
--     (5, 'File 5'),
--     (6, 'File 6'),
--     (7, 'File 7');

INSERT INTO GlobalInfo (ID, PublicKeyTallier, PublicKeyVotingServer, Generator, OrderP) VALUES
    (0, null, null, null, null);