import styled from "styled-components";

/**
 * Generates a progressbar with named steps and bars that can be filled to visually indicate progress.
 *
 * @param {Object} props - The props for the button.
 * @param {string[]} props.array - An array of step names to display in the progress bar.
 * @param {number} props.filled - The number of steps that should be visually marked as completed.
 * @returns {JSX.Element} A progress bar component with labeled steps.
 */
const ProgressBar = ({ array = [], filled = 0 }) => {
  return (
    <Container>
      {array.map((stepName, index) => (
        <NamedBar key={index}>
          <Name>{stepName}</Name>
          <Bar $filled={index < filled} />
        </NamedBar>
      ))}
    </Container>
  );
};

export default ProgressBar;

const Container = styled.div`
  display: flex;
  flex-direction: row;
  justify-content: center;
  padding: 10px;
`;
const NamedBar = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  margin: 0 10px 0 10px;
`;
const Name = styled.p`
  line-height: 1;
  margin: 5px;
`;
const Bar = styled.div`
  width: 170px;
  height: 8px;
  border: 2px solid var(--primary-color);
  background-color: ${({ $filled }) => ($filled ? "#7298b7" : "transparent")};
  border-radius: 5px;
`;
