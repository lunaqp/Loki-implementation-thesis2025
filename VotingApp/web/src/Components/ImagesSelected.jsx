import styled from "styled-components";

//shows list of selected imgs
const ImagesSelected = ({ images, onRemove }) => {
  if (!images.length) return <Empty>(none yet)</Empty>;
  return (
    <Row>
      {images.map((src) => (
        <ImgInList key={src} onClick={() => onRemove(src)} title="Remove">
          {" "}
          {/*click removes*/}
          <Image src={src} alt="" />
        </ImgInList>
      ))}
    </Row>
  );
};
export default ImagesSelected;

const Empty = styled.div`
  opacity: 0.7;
  font-style: italic;
`;

const Row = styled.div`
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
`;

const ImgInList = styled.button`
  padding: 2px;
  background: #fff;
  border: 2px solid rgba(0, 0, 0, 0.15);
  border-radius: 10px;
  cursor: pointer;

  &:hover {
    border-color: var(--primary-color, #2563eb);
  }
`;

const Image = styled.img`
  display: block;
  width: 72px;
  height: 65px;
  object-fit: cover;
  border-radius: 6px;
`;
