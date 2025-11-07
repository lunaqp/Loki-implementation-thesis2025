import styled from "styled-components";
import PageTemplate from "../Components/PageTemplate";
import ScreenTemplate from "../Components/ScreenTemplate";
import { useNavigate, useParams } from "react-router-dom";
import { useApp } from "../Components/AppContext";

const Confirmation = () => {
  const navigate = useNavigate();
  const { electionId } = useParams();
  const { startTimeout } = useApp();
  const { electionName, clearFlow } = useApp();

  const handleFinish = () => {
    if (electionId) {
      startTimeout(Number(electionId), 1 * 60 * 1000); // timeout 6 minutes
    }
    clearFlow();
    navigate("/mypage");
  };

  return (
    <PageTemplate
      progress={6}
      onButtonClick={handleFinish}
      electionName={electionName}
    >
      <ScreenTemplate
        showSecondaryButton={false}
        primaryButtonText="Finish"
        onPrimaryClick={handleFinish}
      >
        <Container>
          <Question>You have now completed the voting process.</Question>
          <Text>
            This is the only confirmation you will see. <br />
            For security reasons, the system will not send you a confirmation
            e-mail with the selected candidate.
          </Text>
        </Container>
      </ScreenTemplate>
    </PageTemplate>
  );
};

export default Confirmation;

const Container = styled.div`
  width: 100%;
  word-wrap: break-word;
  display: flex;
  justify-content: center;
  align-items: center;
  flex-direction: column;
`;

const Question = styled.h1``;

const Text = styled.h2`
  text-align: center;
`;
