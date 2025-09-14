import styled from "styled-components";
import TextBox from "./TextBox";

const MemorableInfoComponent = ({ title, message, children }) => {
  return (
    <Container>
      <TextContainer>
        <TextBox title={title} message={message} />
      </TextContainer>
      <InfoSpace>{children}</InfoSpace>
    </Container>
  );
};

export default MemorableInfoComponent;

const Container = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 30px;
  width: 100%;
  height: 100%;
`;

const TextContainer = styled.div`
  text-align: center;
  max-width: 700px;
`;

const InfoSpace = styled.div`
  width: 350px;
  height: 350px;
  border: 3px solid black;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 100%;
  margin-bottom: 40px;
`;
