import styled from "styled-components";

const TextBox = ({ title, text1, text2, text3, text4, message }) => {
  return (
    <Container>
      <Title>{title}</Title>
      <Text>{text1}</Text>
      <Text>{text2}</Text>
      <Text>{text3}</Text>
      <Text>{text4}</Text>
      <Text>{message}</Text>
    </Container>
  );
};

export default TextBox;

const Title = styled.h2``;

const Text = styled.p`
  font-size: 20px;
`;

const Container = styled.div`
  word-break: break-word;
  width: 100%;
`;
