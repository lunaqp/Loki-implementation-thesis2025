import styled from "styled-components";
import { useNavigate } from "react-router-dom";

const FrontPage = ({ electionId }) => {
  const navigate = useNavigate();

  console.log(electionId);
  return (
    <Page>
      <Header>
        <HeaderContent>
          <Title>My Page</Title>
        </HeaderContent>
      </Header>

      <BodyContainer>
        <h1>Voting System Prototypes</h1>

        <ButtonRow>
          <button
            onClick={() => electionId && navigate(`${electionId}/Welcome`)}
          >
            Election 1
          </button>
        </ButtonRow>
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
  align-items: center;
  width: 1200px;
  gap: 20px;
`;

const ButtonRow = styled.div`
  display: flex;
  gap: 20px;
  margin-top: 20px;
`;
