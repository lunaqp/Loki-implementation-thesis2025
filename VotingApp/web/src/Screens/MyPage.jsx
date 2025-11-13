import styled from "styled-components";
import { useNavigate } from "react-router-dom";
import { useState, useEffect, useMemo } from "react";
import { useApp } from "../Components/AppContext";

const MyPage = () => {
  const navigate = useNavigate();
  const {
    user,
    setElections,
    elections,
    hasUnread,
    setHasUnread,
    getRemainingMs,
  } = useApp();

  // tick every second to count down
  const [, setTick] = useState(0);
  useEffect(() => {
    const id = setInterval(() => setTick((t) => t + 1), 1000);
    return () => clearInterval(id);
  }, []);

  //format miliseconds to clock format eg. 06:00
  const format_ms = (ms) => {
    const s = Math.ceil(ms / 1000); //seconds
    const m = Math.floor(s / 60) //min
      .toString()
      .padStart(2, "0");
    const r = (s % 60).toString().padStart(2, "0");
    return `${m}:${r}`;
  };

  const handleRead = () => {
    setHasUnread(false);
    navigate("/instructions");
  };

  const [tallyStatus, setTallyStatus] = useState(null);

  const fetchTallyVerification = async (electionId) => {
    try {
      const response = await fetch(
        `/api/verify_tally?election_id=${electionId}`
      );

      if (!response.ok) {
        const errText = await response.text();
        throw new Error(
          `Error fetching result of tally verification: ${errText}`
        );
      }

      const data = await response.json();

      return data.verified;
    } catch (error) {
      console.error("Error fetching result of tally verification:", error);
      throw error;
    }
  };

  const fetchElections = async (voterId) => {
    try {
      const response = await fetch(
        `/api/fetch-elections-for-voter?voter_id=${voterId}`
      );

      if (!response.ok) {
        const errText = await response.text();
        throw new Error(`Error fetching elections: ${errText}`);
      }

      const data = await response.json();
      setElections(data.elections);

      return data.elections;
    } catch (error) {
      console.error("Error fetching elections:", error);
      throw error;
    }
  };

  useEffect(() => {
    if (!user) return;

    const voterId = user.user;
    const loadElections = async () => {
      try {
        await fetchElections(voterId);
      } catch (err) {
        console.log(err.message);
      }
    };
    loadElections();
  }, [user]);

  const now = Date.now();

  const { activeElections, finishedElections } = useMemo(() => {
    const active = [];
    const finished = [];
    for (const e of elections) {
      const endTs = new Date(e.end).getTime();
      if (isNaN(endTs)) {
        active.push(e);
        continue;
      } // fallback
      if (endTs > now) active.push(e);
      else finished.push(e);
    }
    return { activeElections: active, finishedElections: finished };
  }, [elections, now]);

  const [resultOpen, setResultOpen] = useState(false);
  const [resultLoading, setResultLoading] = useState(false);
  const [resultError, setResultError] = useState("");
  const [resultData, setResultData] = useState(null);
  const [resultElection, setResultElection] = useState(null);

  const openResults = async (election) => {
    setResultElection(election);
    setResultOpen(true);
    setResultLoading(true);
    setResultError("");
    setResultData(null);
    setTallyStatus(null);

    try {
      const res = await fetch(
        `/api/election-result?election_id=${election.id}`
      );
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      setResultData(data);

      const verified = await fetchTallyVerification(election.id);
      setTallyStatus(verified ? "success" : "error");
    } catch (err) {
      setResultError(String(err));
      setTallyStatus("error");
    } finally {
      setResultLoading(false);
    }
  };

  const closeResults = () => {
    setResultOpen(false);
    setResultElection(null);
    setResultData(null);
    setResultError("");
  };

  return (
    <Page>
      <Header>
        <HeaderContent>
          <Title>Welcome to MyPage!</Title>
          <LogoutButton>Log out</LogoutButton>
        </HeaderContent>
      </Header>

      <BodyContainer>
        <RowHeader>Active elections</RowHeader>
        <ElectionRow>
          <InstructionBox>
            {hasUnread && <NotificationDot />}
            <h2>Instructions & FAQ</h2>
            <ButtonGroup>
              <button className="secondary" onClick={handleRead}>
                Read
              </button>
            </ButtonGroup>
          </InstructionBox>
          {activeElections.length === 0 && (
            <EmptyCard>No active elections</EmptyCard>
          )}
          {activeElections.map((e) => {
            const remaining =
              typeof getRemainingMs === "function" ? getRemainingMs(e.id) : 0;
            const locked = remaining > 0;
            return (
              <ElectionBox key={e.id}>
                <h2>{e.name}</h2>

                {locked && (
                  <TimeoutNote>
                    You are able to vote again in: <b>{format_ms(remaining)}</b>
                  </TimeoutNote>
                )}

                <ButtonGroup>
                  <button
                    disabled={locked}
                    onClick={() => e.id && navigate(`/${e.id}/Welcome`)}
                  >
                    {locked ? "Vote (locked)" : "Vote"}
                  </button>
                </ButtonGroup>
              </ElectionBox>
            );
          })}
        </ElectionRow>

        {/* Finished elections */}
        <RowHeader>Finished elections</RowHeader>
        <ElectionRow>
          {finishedElections.length === 0 && (
            <EmptyCard>No finished elections</EmptyCard>
          )}
          {finishedElections.map((e) => (
            <ElectionBox key={e.id}>
              <h2>{e.name}</h2>
              <ButtonGroup>
                <button onClick={() => openResults(e)}>Show result</button>
              </ButtonGroup>
            </ElectionBox>
          ))}
        </ElectionRow>
      </BodyContainer>

      {/* Modal */}
      {resultOpen && (
        <ModalOverlay onClick={closeResults}>
          {/*to be able to close by clicking background*/}
          <ModalCard onClick={(e) => e.stopPropagation()}>
            <ModalHeader>
              <h3>Results — {resultElection?.name}</h3>
              <CloseX onClick={closeResults}>×</CloseX>
            </ModalHeader>

            {resultLoading && <ModalBody>Loading results…</ModalBody>}
            {resultError && (
              <ModalBody style={{ color: "red" }}>{resultError}</ModalBody>
            )}
            {!resultLoading && !resultError && resultData && (
              <ModalBody>
                <h4>Candidates:</h4>
                {Array.isArray(resultData.result) ? (
                  <ResultList>
                    {resultData.result.map((r) => (
                      <li key={r.candidateid}>
                        <span>{r.candidate_name}</span>
                        <b>{r.votes} votes</b>
                      </li>
                    ))}
                  </ResultList>
                ) : (
                  <div>No result available yet.</div>
                )}
              </ModalBody>
            )}
            <ModalFooter>
              {tallyStatus === "success" && (
                <span style={{ color: "green", fontWeight: "600" }}>
                  Tally verified!
                </span>
              )}
              {tallyStatus === "error" && (
                <span style={{ color: "red", fontWeight: "600" }}>
                  Error verifying tally
                </span>
              )}
            </ModalFooter>
          </ModalCard>
        </ModalOverlay>
      )}
    </Page>
  );
};

export default MyPage;

const Page = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  min-height: 100vh;
  width: 100%;
  overflow: hidden;
`;

const Header = styled.div`
  display: flex;
  flex-direction: row;
  justify-content: center;
  align-items: center;
  height: 110px;
  width: 100%;
  background-color: var(--primary-color);
  box-shadow: 0 2px 4px 0 rgba(0, 0, 0, 0.2);
`;

const HeaderContent = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 1200px;
`;

const Title = styled.h1`
  font-family: inherit;
`;

const BodyContainer = styled.div`
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: flex-start;
  width: 1200px;
  gap: 20px;
`;

const RowHeader = styled.h3`
  margin: 28px 0 0px;
  font-size: 18px;
  font-weight: 700;
`;

const ElectionRow = styled.div`
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 40px;
  width: 100%;
  margin-top: 0px;
  justify-items: start;
  align-items: start;
`;

const BaseBox = styled.div`
  width: 300px;
  padding: 20px 20px 30px;
  border-radius: 12px;
  background: var(--secondary-color);
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
  text-align: center;
  border: 3px solid var(--primary-color);

  h2 {
    margin-bottom: 12px;
  }
`;

const ElectionBox = styled(BaseBox)``;

const InstructionBox = styled(BaseBox)`
  position: relative;
  background-color: var(--primary-color);
  border-color: var(--primary-color);
`;

const EmptyCard = styled.div`
  width: 300px;
  justify-self: start;
  opacity: 0.7;
  font-size: 14px;
  padding: 12px 16px;
  margin-bottom: 40px;
  border-radius: 8px;
  background: #f1f5f9;
  border: 1px solid #e5e7eb;
  margin: 0;
`;

const ButtonGroup = styled.div`
  display: flex;
  gap: 12px;
  justify-content: center;

  button {
    padding: 10px 16px;
    border: none;
    border-radius: 8px;
    background: var(--primary-color);
    color: white;
    font-weight: 600;
    cursor: pointer;
  }

  button.secondary {
    background: rgb(50, 50, 50);
    color: white;
  }

  button:disabled {
    opacity: 0.6;
    cursor: not-allowed;
    background: #9aa0a6;
  }
`;

const LogoutButton = styled.button`
  padding: 10px 20px;
  border: none;
  border-radius: 8px;
  background: rgb(50, 50, 50);
  color: white;
  font-weight: 600;
  cursor: pointer;

  &:hover {
    background-color: rgb(225, 225, 225);
    color: black;
    border-color: rgb(50, 50, 50);
  }
`;

const NotificationDot = styled.div`
  position: absolute;
  top: -6px;
  right: -6px;
  width: 18px;
  height: 18px;
  background: #da4b4b;
  border-radius: 50%;
  border: 2px solid white;
`;

const TimeoutNote = styled.p`
  margin: 6px 0 12px;
  font-size: 14px;
`;

const ModalOverlay = styled.div`
  position: fixed;
  inset: 0;
  z-index: 40;
  background: rgba(0, 0, 0, 0.45);
  display: grid;
  place-items: center;
`;

const ModalCard = styled.div`
  width: 560px;
  max-width: calc(100% - 32px);
  background: white;
  border-radius: 12px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.25);
  overflow: hidden;
`;

const ModalHeader = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  border-bottom: 1px solid #e5e7eb;

  h3 {
    margin: 0;
    font-size: 18px;
  }
`;

const ModalFooter = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  border-top: 1px solid #e5e7eb;

  h3 {
    margin: 0;
    font-size: 18px;
  }
`;

const CloseX = styled.button`
  border: 0;
  background: transparent;
  font-size: 24px;
  line-height: 1;
  cursor: pointer;
  color: #64748b;
  &:hover {
    color: #111827;
  }
`;

const ModalBody = styled.div`
  padding: 16px;

  h4 {
    margin: 0 0 8px;
  }
`;

const ResultList = styled.ul`
  list-style: none;
  padding: 0;
  margin: 0;
  display: grid;
  gap: 10px;

  li {
    display: flex;
    align-items: center;
    justify-content: space-between;
    border: 1px solid #e5e7eb;
    border-radius: 10px;
    padding: 10px 12px;
    background: #fff;
  }
`;
