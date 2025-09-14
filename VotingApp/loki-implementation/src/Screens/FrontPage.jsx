import styled from "styled-components";
import { useNavigate } from "react-router-dom";

const FrontPage = ({ electionId }) => {
  const navigate = useNavigate();

  console.log(electionId);
  return (
    electionId && (
      <Container>
        <h1>Voting System Prototypes</h1>
        <ButtonContainer>
          <button
            variant="primary"
            onClick={() => navigate(`${electionId}/Welcome`)}
          >
            Prototype
          </button>
        </ButtonContainer>
      </Container>
    )
  );
};

export default FrontPage;

const Container = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
`;

const ButtonContainer = styled.div`
  display: flex;
  gap: 20px;
  margin-top: 20px;
`;
