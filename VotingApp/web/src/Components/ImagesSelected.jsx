import styled from "styled-components";

//shows list of selected imgs
const ImagesSelected = ({ images, onRemove }) => {
  console.log("Selected images:", images);
  if (!images.length) return <Empty>(none yet)</Empty>;
  return (
    <Row>
      {images.map((cbrimage) => (
        <ImgInList
          key={cbrimage.cbrindex}
          onClick={() => onRemove(cbrimage)}
          title="Remove"
        >
          {" "}
          {/*click removes*/}
          <Image src={`/images/${cbrimage.image}`} alt={cbrimage.image} />
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
  height: 70px;
  object-fit: cover;
  border-radius: 6px;
`;
