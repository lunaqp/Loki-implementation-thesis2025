import styled from "styled-components";
import { useNavigate } from "react-router-dom";
import { useState, useEffect } from "react";
import { useApp } from "../Components/AppContext";

const MyPage = () => {
  const navigate = useNavigate();
  const { user, setElections, elections, hasUnread, setHasUnread } = useApp();

  const handleRead = () => {
    setHasUnread(false);
    navigate("/instructions");
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
      console.log(data.elections);
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

  console.log(user);
  return (
    <Page>
      <Header>
        <HeaderContent>
          <Title>Welcome to MyPage!</Title>
          <LogoutButton>Log out</LogoutButton>
        </HeaderContent>
      </Header>

      <BodyContainer>
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

          {elections.map((election) => (
            <ElectionBox key={election.id}>
              <h2>{election.name}</h2>
              <ButtonGroup>
                <button
                  onClick={() =>
                    election.id && navigate(`/${election.id}/Welcome`)
                  }
                >
                  Vote
                </button>
              </ButtonGroup>
            </ElectionBox>
          ))}
        </ElectionRow>
      </BodyContainer>
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

const ElectionRow = styled.div`
  display: flex;
  gap: 60px;
  margin-top: 60px;
  justify-content: flex-start;
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
