import { useNavigate } from "react-router-dom";
import styled from "styled-components";
import Button from "./Button";

const ScreenTemplate = ({
  children,
  onPrimaryClick,
  nextRoute,
  prevRoute,
  showPrimaryButton = true,
  showSecondaryButton = true,
  secondaryButtonText = "Back",
  primaryButtonText = "Next",
  adjustableHeight,
  buttonUnselectable,
}) => {
  const navigate = useNavigate();

  const handleSecondaryClick = () => {
    if (prevRoute) {
      navigate(prevRoute);
    }
  };

  const handlePrimaryClick = () => {
    if (nextRoute) {
      navigate(nextRoute);
    }
  };

  return (
    <>
      <ScreenWrapper $adjustableHeight={adjustableHeight}>
        {children}
        <ButtonContainer>
          {showSecondaryButton && (
            <LeftButtonWrapper>
              <Button variant="secondary" onClick={handleSecondaryClick}>
                {secondaryButtonText}
              </Button>
            </LeftButtonWrapper>
          )}
          {showPrimaryButton && (
            <RightButtonWrapper>
              <Button
                variant="primary"
                onClick={onPrimaryClick || handlePrimaryClick}
                unselectable={buttonUnselectable}
              >
                {primaryButtonText}
              </Button>
            </RightButtonWrapper>
          )}
        </ButtonContainer>
      </ScreenWrapper>
    </>
  );
};

export default ScreenTemplate;

const ScreenWrapper = styled.div`
  width: 100%;
  min-height: 600px;
  height: auto;
  border-radius: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 30px 60px 60px 60px;
  background-color: var(--secondary-color);
  border: 1px solid black;
`;

// const ScreenWrapper = styled.div`
//   width: 1100px;
//   ${({ $adjustableHeight }) =>
//     $adjustableHeight
//       ? `min-height: 600px;
//         height: auto;
//         padding-bottom: 70px;`
//       : `height: 600px;`}
//   border-radius: 20px;
//   display: flex;
//   align-items: center;
//   justify-content: center;
// `;

const ButtonContainer = styled.div`
  width: 100%;
  position: absolute;
  bottom: 30px;
  height: 40px;
`;

const LeftButtonWrapper = styled.div`
  position: absolute;
  left: 80px;
  bottom: 0;
`;

const RightButtonWrapper = styled.div`
  position: absolute;
  right: 80px;
  bottom: 0;
`;
