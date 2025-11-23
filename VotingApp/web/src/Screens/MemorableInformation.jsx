import styled from "styled-components";
import PageTemplate from "../Components/PageTemplate";
import MemorableInfoComponent from "../Components/MemorableInfoComponent";
import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import PopUp from "../Components/PopUp";
import ScreenTemplate from "../Components/ScreenTemplate";
import { useApp } from "../Components/AppContext";

const MemorableInformation = () => {
  const { electionId } = useParams();
  const nextRoute = `/${electionId}/Confirmation`;
  const prevRoute = `/${electionId}/CandidateSelection`;
  const [showPopUp, setShowPopUp] = useState(false);
  const { setImageFilename, imageFilename, electionName, clearFlow } = useApp();
  const navigate = useNavigate();

  const navigateToMypage = () => {
    clearFlow();
    navigate("/mypage");
  };

  // generating word from image filename. For example "hockey_stick_11s.jpg".
  const createImageText = (imageFilename) => {
    const imagetext = imageFilename
      .replace(/^./, (c) => c.toUpperCase()) // -> Hockey_stick_11s.jpg
      .slice(0, -8) // -> hockey_stick
      .replaceAll("_", " ") // -> hockey stick
      .replace(/\d+$/, ""); // removing ekstra digit. For example in bow1, bow2, and bow3.
    return imagetext;
  };
  const handleNextClick = () => {
    setShowPopUp(true);
  };

  const handleConfirm = () => {
    setShowPopUp(false);
    navigate(nextRoute);
    setImageFilename(null);
  };

  const handleCancel = () => {
    setShowPopUp(false);
  };

  return (
    imageFilename && (
      <PageTemplate
        progress={5}
        onButtonClick={navigateToMypage}
        electionName={electionName}
      >
        <ScreenTemplate
          nextRoute={nextRoute}
          onPrimaryClick={handleNextClick}
          prevRoute={prevRoute}
          showSecondaryButton={false}
        >
          <Container>
            <ContentWrapper>
              <MemorableInfoComponent
                title="IMPORTANT!"
                message={`Make sure you remember the below image in case you want to change your vote later.`}
                imageFilename={imageFilename}
                imagetext={createImageText(imageFilename)}
              />
            </ContentWrapper>
          </Container>
        </ScreenTemplate>
        {showPopUp && (
          <PopUp
            title="Attention!"
            message="This is your last chance to memorise the image. You will not be able to come back to view this information again!"
            confirm={handleConfirm}
            cancel={handleCancel}
            nextButtonText="I remember"
            backButtonText="Go back"
          />
        )}
      </PageTemplate>
    )
  );
};

export default MemorableInformation;

const Container = styled.div`
  width: 100%;
  height: 100%;
  word-wrap: break-word;
  display: flex;
  justify-content: center;
  flex-direction: column;
  align-items: flex-start;
  padding-top: 30px;
`;

const ContentWrapper = styled.div`
  display: flex;
  flex-direction: column;
  gap: 0px;
  align-items: center;
  padding: 0 0 80px 0;
  width: 100%;
`;
