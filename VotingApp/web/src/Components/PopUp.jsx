import styled from "styled-components";
import Button from "./Button";
import TextBox from "./TextBox";

/*Reusable pop up component with props to change title, message, button text*/

const PopUp = ({
  title,
  message,
  confirm,
  cancel,
  backButtonText,
  nextButtonText,
}) => {
  return (
    <Container>
      <PopUpBox>
        <TextBox title={title} text1={message} />
        <Buttons>
          <Button variant="secondary" onClick={cancel}>
            {backButtonText}
          </Button>
          <Button variant="primary" onClick={confirm}>
            {nextButtonText}
          </Button>
        </Buttons>
      </PopUpBox>
    </Container>
  );
};

export default PopUp;

const Container = styled.div`
  width: 100%;
  height: 100%;
  position: absolute;
  top: 0;
  left: 0;
  z-index: 2;
  background-color: rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(3px);
  border-radius: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
`;

const PopUpBox = styled.div`
  background-color: var(--secondary-color);
  padding: 30px;
  border-radius: 10px;
  width: 400px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  text-align: center;
  border: 2px solid black;
`;

const Buttons = styled.div`
  display: flex;
  justify-content: space-between;
`;
