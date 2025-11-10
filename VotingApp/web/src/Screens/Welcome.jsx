import PageTemplate from "../Components/PageTemplate";
import ScreenTemplate from "../Components/ScreenTemplate";
import styled from "styled-components";
import { useParams, useNavigate } from "react-router-dom";
import { useApp } from "../Components/AppContext";
import { useEffect } from "react";

const Welcome = () => {
  const { electionId } = useParams();
  const navigate = useNavigate();
  const nextRoute = `/${electionId}/VoteCheck`;
  const prevRoute = "/Mypage";
  const { elections, electionName, setElectionName, clearFlow } = useApp();

  const navigateToMypage = () => {
    clearFlow();
    navigate("/mypage");
  };

  useEffect(() => {
    const election = elections.find(
      (election) => Number(election.id) === Number(electionId)
    );

    election ? setElectionName(election.name) : setElectionName(null);
  }, [electionId, elections]);

  return (
    <PageTemplate
      progress={1}
      onButtonClick={navigateToMypage}
      electionName={electionName}
    >
      <ScreenTemplate
        nextRoute={nextRoute}
        prevRoute={prevRoute}
        showSecondaryButton={false}
        primaryButtonText="Start"
      >
        <ColumnWrapper>
          <InstructionsTitle>Welcome to the voting process!</InstructionsTitle>
          <InstructionsWrapper>
            <Text>
              This system might be a little different from what you are used to.
              <br />
              If you are ever in doubt about the voting process, you can always
              go back to MyPage by clicking the "Exit voting process" button and
              read the step by step guide in the “Instructions & FAQ” tab.
              <br />
              Happy voting!{" "}
            </Text>
          </InstructionsWrapper>
        </ColumnWrapper>
      </ScreenTemplate>
    </PageTemplate>
  );
};

export default Welcome;

const InstructionsTitle = styled.h1`
  margin: 0px;
  line-height: 1;
`;

const ColumnWrapper = styled.div`
  display: flex;
  gap: 100px;
  flex-direction: column;
  align-items: center;
  padding-bottom: 70px;
  width: 100%;
`;

const InstructionsWrapper = styled.div`
  display: flex;
  justify-content: center;
  width: 100%;
`;

const Text = styled.div`
  width: 80%;
  line-height: 1.2;
  font-size: 20px;
  text-align: center;
`;
