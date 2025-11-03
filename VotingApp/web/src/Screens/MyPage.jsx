import styled from "styled-components";
import { useNavigate } from "react-router-dom";
import { useState, useEffect } from "react";
import { useApp } from "../Components/AppContext";

const MyPage = () => {
  const navigate = useNavigate();
  const [showPopup, setShowPopup] = useState(false);
  const { user, setElections, elections } = useApp();

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
          <Title>Welcome Aja!</Title>
          <LogoutButton>Log out</LogoutButton>
        </HeaderContent>
      </Header>

      <BodyContainer>
        <ElectionRow>
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
                <button onClick={() => setShowPopup(true)}>Verify</button>
              </ButtonGroup>
            </ElectionBox>
          ))}
        </ElectionRow>
      </BodyContainer>
      {showPopup && (
        <PopupOverlay>
          <PopupBox>
            <PopupHeader>
              <h2>Verify Vote</h2>
              <CloseButton onClick={() => setShowPopup(false)}>×</CloseButton>
            </PopupHeader>
            <PopupContent>Your vote has been included!</PopupContent>
          </PopupBox>
        </PopupOverlay>
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

const ElectionRow = styled.div`
  display: flex;
  gap: 60px;
  margin-top: 60px;
  justify-content: flex-start;
`;

const ElectionBox = styled.div`
  width: 300px;
  padding: 20px;
  border-radius: 12px;
  background: #f9f9f9;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
  text-align: center;
  border: 3px solid rgba(0, 0, 0, 0.2);

  h2 {
    margin-bottom: 20px;
  }
`;

const ButtonGroup = styled.div`
  display: flex;
  gap: 12px;
  justify-content: center;

  button {
    padding: 10px 16px;
    border: none;
    border-radius: 8px;
    background: var(--primary-color, #2563eb);
    color: white;
    font-weight: 600;
    cursor: pointer;
  }

  button:last-child {
    background: #6b7280;
  }
`;

const LogoutButton = styled.button`
  padding: 8px 20px;
  border: none;
  border-radius: 8px;
  background: var(white);
  color: black;
  font-weight: 600;
  cursor: pointer;

  &:hover {
    background: #374151;
    color: white;
  }
`;

const PopupOverlay = styled.div`
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 3;
`;

const PopupBox = styled.div`
  width: 500px;
  height: 300px;
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
  text-align: center;
`;

const PopupHeader = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  position: relative;
  font-size: 25px;

  h2 {
    margin: 0px;
    text-align: center;
  }
`;

const PopupContent = styled.p`
  margin-top: 26px;
  font-size: 20px;
  text-align: center;
`;

const CloseButton = styled.button`
  position: absolute;
  right: 0;
  top: 0;
  background: none;
  border: none;
  font-size: 30px;
  font-weight: bold;
  cursor: pointer;
  color: #333;

  &:hover {
    color: red;
  }
`;
