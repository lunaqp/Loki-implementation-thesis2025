import styled from "styled-components";
import PageTemplate from "../Components/PageTemplate";
import ScreenTemplate from "../Components/ScreenTemplate";
import { useNavigate } from "react-router-dom";
import { useApp } from "../Components/AppContext";

const Confirmation = () => {
  const nextRoute = "/Mypage";
  const navigate = useNavigate();
  const { electionName, clearFlow } = useApp();

  const navigateToMypage = () => {
    clearFlow();
    navigate("/mypage");
  };

  return (
    <PageTemplate
      progress={6}
      onButtonClick={navigateToMypage}
      electionName={electionName}
    >
      <ScreenTemplate
        showSecondaryButton={false}
        primaryButtonText="Finish"
        onPrimaryClick={navigateToMypage}
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
