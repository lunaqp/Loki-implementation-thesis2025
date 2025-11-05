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
  const navigate = useNavigate();
  const { imageFilename } = useApp();

  const handleNextClick = () => {
    setShowPopUp(true);
  };

  const handleConfirm = () => {
    setShowPopUp(false);
    navigate(nextRoute);
  };

  const handleCancel = () => {
    setShowPopUp(false);
  };

  return (
    imageFilename && (
      <PageTemplate progress={5} adjustableHeight={true}>
        <ScreenTemplate
          nextRoute={nextRoute}
          onPrimaryClick={handleNextClick}
          prevRoute={prevRoute}
          showSecondaryButton={false}
          adjustableHeight={true}
        >
          <Container>
            <ContentWrapper>
              <MemorableInfoComponent
                title="IMPORTANT!"
                message={`You have to remember the below image in case you want to change your vote later.`}
              >
                <img
                  src={`/images/${imageFilename}`}
                  alt={`${imageFilename}`}
                  style={{ maxWidth: "100%", maxHeight: "100%" }}
                />
              </MemorableInfoComponent>
            </ContentWrapper>
          </Container>
        </ScreenTemplate>
        {showPopUp && (
          <PopUp
            title="Attention!"
            message="Make sure you remember the information displayed! This is important if you want to change your vote. You will not be able to come back to view this information again!"
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
