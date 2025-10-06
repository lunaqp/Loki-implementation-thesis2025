import styled from "styled-components";
import ProgressBar from "./ProgressBar.jsx";

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
  steps = [
    "Welcome",
    "Vote Check",
    "Previous Votes",
    "Candidate Selection",
    "Memorable Information",
    "Confirmation",
  ],
}) => {
  /**
   * A styled container for content that is placed inside the screen area of the page template.
   * This component wraps and centers the content inside a styled screen box with specific dimensions.
   *
   * @param {Object} props - The props passed to the Screen component.
   * @param {ReactNote} props.children - The content to display inside the <Screen> element (this can include any React components or JSX).
   * @returns {JSX.Element} A styled <Screen> component containing the children passed to it.
   */

  return (
    <Page>
      <Header>
        <HeaderContent>
          <Title>Election Process</Title>
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
  //border: 1px solid black;
`;

// const StyledScreen = styled.div`
//   width: 1100px;
//   border: 1px solid black;
//   ${({ $adjustableHeight }) =>
//     $adjustableHeight
//       ? `min-height: 600px;
//         height: auto;`
//       : `height: 600px;`}
//   border-radius: 20px;
//   background-color: var(--secondary-color);
//   display: flex;
//   align-items: center;
//   justify-content: center;
//   position: relative;
//   margin: 0 0 60px 0;
//   padding: 30px 60px 30px 60px; // If padding is updated it also needs to be updated in CandidateSelection.js and MemorableInformation.js to maintain proper blurring.
// `;
