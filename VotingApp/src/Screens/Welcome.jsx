import PageTemplate from "../Components/PageTemplate";
import ScreenTemplate from "../Components/ScreenTemplate";
import styled from "styled-components";
import { useParams } from "react-router-dom";

const Welcome = () => {
  const { electionId } = useParams();
  const nextRoute = `/${electionId}/VoteCheck`;
  const prevRoute = "/";

  return (
    <PageTemplate progress={1}>
      <ScreenTemplate
        nextRoute={nextRoute}
        prevRoute={prevRoute}
        showSecondaryButton={false}
        primaryButtonText="Start"
      >
        <ColumnWrapper>
          <InstructionsTitle>Welcome to the voting process</InstructionsTitle>
          <InstructionsWrapper>
            <Text>
              This system might be a little different from what you are used to.
              This is because it is designed to help prevent voter coercion.
              After casting a vote, you will be shown an image that you will
              need to remember in case you want to change your vote later on.
              The process will start with checking if you have voted before.{" "}
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
  width: 60%;
  line-height: 1.2;
  font-size: 20px;
  text-align: center;
`;
