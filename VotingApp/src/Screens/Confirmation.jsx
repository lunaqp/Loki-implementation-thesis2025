import styled from "styled-components";
import PageTemplate from "../Components/PageTemplate";
import ScreenTemplate from "../Components/ScreenTemplate";

const Confirmation = () => {
  const nextRoute = "/";

  return (
    <PageTemplate progress={6}>
      <ScreenTemplate
        nextRoute={nextRoute}
        showSecondaryButton={false}
        primaryButtonText="Finish"
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
