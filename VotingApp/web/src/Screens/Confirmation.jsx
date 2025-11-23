import "../Components/Spinner.css";
import styled from "styled-components";
import PageTemplate from "../Components/PageTemplate";
import ScreenTemplate from "../Components/ScreenTemplate";
import { useNavigate } from "react-router-dom";
import { useApp } from "../Components/AppContext";
import { useEffect, useState } from "react";

const Confirmation = () => {
  const navigate = useNavigate();
  const { electionName, clearFlow } = useApp();
  const [ballotVerified, setBallotVerified] = useState(null);

  const handleFinish = () => {
    clearFlow();
    navigate("/mypage");
  };

  // Simulation a waiting period for ballot to be appended to BB and then verified from there.
  useEffect(() => {
    const timer = setTimeout(() => {
      setBallotVerified(true);
    }, 1000 * 60 * 3);
    return () => clearTimeout(timer);
  }, []);

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
          <Question>Your vote has now been cast.</Question>
          <Text>
            For security reasons this is the only confirmation you will see.{" "}
            <br />
            Your vote will be finalised within the next few minutes. You now
            have the option to wait for a verification that your ballot has been
            correctly registered.
          </Text>
          {ballotVerified === null && (
            <VerificationContainer>
              <span className="loader"></span>
              <SpinnerText>Awaiting verification...</SpinnerText>
            </VerificationContainer>
          )}
          {ballotVerified !== null &&
            (ballotVerified ? (
              <VerificationText color="green">
                Ballot succesfully verified
              </VerificationText>
            ) : (
              <VerificationText color="red">
                Ballot verification unsuccessful.{" "}
              </VerificationText>
            ))}

          <Text>
            Click the “Finish” button to navigate back to MyPage.{" "}
            {/*You will now
            see a timeout on this election, and you will be able to change your
            vote once the timer is up. */}
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

const Text = styled.p`
  font-size: 20px;
  text-align: left;
  width: 800px;
`;

const SpinnerText = styled.p`
  font-size: 20px;
`;

const VerificationText = styled.p`
  color: ${({ color }) => color || "black"};
  font-weight: bold;
  font-size: 24px;
`;

const VerificationContainer = styled.div`
  display: flex;
  flex-direction: row;
  gap: 20px;
  justify-content: center;
  align-items: center;
`;
