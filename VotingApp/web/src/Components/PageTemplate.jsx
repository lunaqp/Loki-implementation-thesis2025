import styled from "styled-components";
import ProgressBar from "./ProgressBar.jsx";
import Button from "./Button.jsx";

/**
 * A template for a page layout that includes a progress bar and a screen section.
 * The progress bar indicates the progress of a series of steps, while the screen can display dynamic content.
 *
 * @param {Object} props - The props passed to the page template.
 * @param {ReactNode} props.children - The content to display inside the <Screen> element (this can include any React components or JSX).
 * @param {number} props.progress - The number of bars to be filled in on the progress bar, indicating progress  (should be an integer between 0 and the total number of steps).
 * @returns {JSX.Element} A styled page layout that includes a progress bar and a screen to display dynamic content.
 */
const PageTemplate = ({
  children,
  progress,
  columnLayout,
  adjustableHeight,
  onButtonClick,
  electionName,
  steps = [
    "Welcome",
    "Vote Check",
    "Previous Votes",
    "Candidate Selection",
    "Memorable Information",
    "Confirmation",
  ],
}) => {
  return (
    <Page>
      <Header>
        <HeaderContent>
          <Title>{electionName}</Title>
          <Button variant="primary" onClick={onButtonClick}>
            Exit voting process
          </Button>
        </HeaderContent>
      </Header>
      <BodyContainer>
        <ProgressBar array={steps} filled={progress} />
        <StyledScreen
          columnLayout={columnLayout}
          $adjustableHeight={adjustableHeight}
        >
          {children}
        </StyledScreen>
      </BodyContainer>
    </Page>
  );
};

export default PageTemplate;

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
  padding-bottom: 60px;
`;
const StyledScreen = styled.div`
  width: 1200px;
  height: auto;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
`;
