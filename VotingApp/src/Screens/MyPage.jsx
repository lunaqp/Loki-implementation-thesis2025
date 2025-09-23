import styled from "styled-components";
import { useNavigate } from "react-router-dom";

const FrontPage = ({ electionId }) => {
  const navigate = useNavigate();

  console.log(electionId);
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
          <ElectionBox>
            <h2>Election 1</h2>
            <ButtonGroup>
              <button
                onClick={() => electionId && navigate(`/${electionId}/Welcome`)}
              >
                Vote
              </button>
              <button>Verify</button>
            </ButtonGroup>
          </ElectionBox>
          <ElectionBox>
            <h2>Election 2</h2>
            <ButtonGroup>
              <button
                onClick={() => electionId && navigate(`/${electionId}/Welcome`)}
              >
                Vote
              </button>
              <button>Verify</button>
            </ButtonGroup>
          </ElectionBox>
        </ElectionRow>
      </BodyContainer>
    </Page>
  );
};

export default FrontPage;

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
