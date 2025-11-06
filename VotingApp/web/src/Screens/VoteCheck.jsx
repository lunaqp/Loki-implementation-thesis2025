import styled from "styled-components";
import PageTemplate from "../Components/PageTemplate";
import Button from "../Components/Button";
import ScreenTemplate from "../Components/ScreenTemplate";
import { useNavigate, useParams } from "react-router-dom";
import { useApp } from "../Components/AppContext";

const VoteCheck = () => {
  const navigate = useNavigate();
  const { electionId } = useParams();
  const { setPreviousVotes, previousVotes } = useApp();

  const yesRoute = `/${electionId}/PreviousVotes`;
  const noRoute = `/${electionId}/CandidateSelection`;
  const prevRoute = `/${electionId}/Welcome`;

  const navigateToMypage = () => navigate("/mypage");

  return (
    <PageTemplate progress={2} onButtonClick={navigateToMypage}>
      <ScreenTemplate showPrimaryButton={false} prevRoute={prevRoute}>
        <ContentWrapper>
          <Question>Did you already cast a vote in this election?</Question>

          <ButtonContainer>
            <Button
              variant="primary"
              onClick={() => {
                setPreviousVotes([]); // Setting previous votes to an empty list if voter has not voted before.
                console.log(
                  "Previous votes list registered as:",
                  previousVotes
                );
                navigate(noRoute, {
                  state: {
                    from: `/${electionId}/VoteCheck`,
                  },
                });
              }}
            >
              No
            </Button>
            <Button
              variant="primary"
              onClick={() => {
                navigate(yesRoute);
              }}
            >
              Yes
            </Button>
          </ButtonContainer>
          <p>
            If this is your first time voting in this election, select “No”
            <br />
            If you want to change a previously cast vote, select “Yes”
            <br />
            If you are being coerced, and have already voted in this election,
            you can select “No” and the system will automatically know not to
            count the vote you are about to cast.
          </p>
        </ContentWrapper>
      </ScreenTemplate>
    </PageTemplate>
  );
};

export default VoteCheck;

const ContentWrapper = styled.div`
  display: flex;
  flex-direction: column;
  gap: 50px;
  align-items: center;
`;

const Question = styled.h1`
  margin: 0;
`;

const ButtonContainer = styled.div`
  display: flex;
  justify-content: center;
  gap: 100px;
  width: 100%;
  margin-top: 10px;
`;
