import styled from "styled-components";
import TextBox from "./TextBox";

const MemorableInfoComponent = ({
  title,
  message,
  imageFilename,
  imagetext,
}) => {
  return (
    <Container>
      <TextContainer>
        <TextBox title={title} message={message} />
      </TextContainer>
      <InfoSpace>
        <MemImage src={`/images/${imageFilename}`} alt={`${imageFilename}`} />
        <ImageText>{imagetext}</ImageText>
      </InfoSpace>
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
  max-width: 900px;
`;

const InfoSpace = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
`;

const MemImage = styled.img`
  width: 350px;
  height: 350px;
  border: 3px solid black;
`;

const ImageText = styled.p`
  line-height: 0;
  font-size: 40px;
  font-weight: bold;
`;
