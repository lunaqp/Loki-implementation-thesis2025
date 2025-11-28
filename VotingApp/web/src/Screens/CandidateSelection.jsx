import styled from "styled-components";
import PageTemplate from "../Components/PageTemplate";
import { useState, useEffect } from "react";
import PopUp from "../Components/PopUp";
import ScreenTemplate from "../Components/ScreenTemplate";
import { useNavigate, useParams, useLocation } from "react-router-dom";
import { useApp } from "../Components/AppContext";

const CandidateSelection = () => {
  const location = useLocation();
  const { electionId } = useParams();
  const navigate = useNavigate();
  const nextRoute = `/${electionId}/MemorableInformation`;
  const prevRoute = location.state?.from || `/${electionId}/PreviousVotes`;
  const {
    previousVotes,
    setImageFilename,
    electionName,
    clearFlow,
    startTimeout,
  } = useApp();
  const [candidates, setCandidates] = useState();

  const navigateToMypage = () => {
    clearFlow();
    navigate("/mypage");
  };

  useEffect(() => {
    fetch(`/api/bulletin/candidates?election_id=${electionId}`)
      .then((res) => res.json())
      .then((data) => {
        setCandidates(data.candidates);
      })
      .catch((err) => console.error("Error fetching candidates:", err));
  }, []);

  const candidateNames =
    candidates && candidates.map((candidate) => candidate.name);

  const [showPopUp, setShowPopUp] = useState(false);

  const [selectedCandidate, setSelectedCandidate] = useState("");

  const handleNextClick = () => {
    if (!selectedCandidate) return;
    setShowPopUp(true);
  };

  const handleConfirm = () => {
    setShowPopUp(false);

    // Finding the relevant index for the chosen candidate
    const selectedCandidateIndex =
      candidates.findIndex((c) => c.name === selectedCandidate) + 1; // + 1 to start counting from 1

    // Elements for ballot:
    const v = selectedCandidateIndex;
    const election_id = electionId;
    const lv_list = previousVotes;

    sendBallot(v, lv_list, election_id);

    navigate(nextRoute);
  };

  const handleCancel = () => {
    setShowPopUp(false);
  };

  const handleChange = (e) => {
    setSelectedCandidate(e.target.value);
  };

  async function sendBallot(v, lv_list, election_id) {
    try {
      const response = await fetch("/api/send-ballot", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ v, lv_list, election_id }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to send ballot");
      }

      const data = await response.json();
      setImageFilename(data.image);
      console.log("API response from Voting Server:", data);
      startTimeout(Number(electionId), 6 * 60 * 1000); // timeout 6 minutes
    } catch (err) {
      console.error("API error:", err);
    }
  }

  return (
    candidates && (
      <PageTemplate
        progress={4}
        onButtonClick={navigateToMypage}
        electionName={electionName}
      >
        <ScreenTemplate
          nextRoute={null}
          onPrimaryClick={handleNextClick}
          prevRoute={prevRoute}
          primaryButtonText="Cast vote"
          buttonUnselectable={!selectedCandidate}
        >
          <ContentWrapper>
            <Wrapper>
              <Title>Candidate Selection</Title>
              <Text>
                Vote for a candidate by clicking their name.
                <br /> You can only choose <strong>one</strong> candidate.
              </Text>
              {candidateNames.map((candidate) => {
                return (
                  <CandidateContainer>
                    <StyledInput
                      type="radio"
                      id={`${candidate}`}
                      name="candidate"
                      value={`${candidate}`}
                      onChange={handleChange}
                      checked={selectedCandidate === `${candidate}`}
                    />
                    <StyledLabel htmlFor={candidate}>{candidate}</StyledLabel>
                  </CandidateContainer>
                );
              })}
            </Wrapper>
          </ContentWrapper>
        </ScreenTemplate>
        {showPopUp && (
          <PopUp
            title="Confirmation"
            message={
              <>
                You are now voting for <strong>{selectedCandidate}</strong>. If
                this is the intended candidate, click “Cast Vote”. If you want
                to change your candidate choice, click “Change Vote”
              </>
            }
            confirm={handleConfirm}
            cancel={handleCancel}
            nextButtonText="Cast vote"
            backButtonText="Change vote"
          />
        )}
      </PageTemplate>
    )
  );
};

export default CandidateSelection;

const Title = styled.h1`
  line-height: 1;
  margin-top: 0;
`;

const Text = styled.p`
  font-size: 20px;
`;

const ContentWrapper = styled.div`
  width: 100%;
  height: 80%;
  display: flex;
  align-items: center;
  flex-direction: column;
  justify-content: flex-start;
  gap: 5px;
`;

const Wrapper = styled.div`
  width: 100%;
  height: 80%;
  display: flex;
  align-items: flex-start;
  flex-direction: column;
  justify-content: flex-start;
  gap: 5px;
  /* padding: 0 0 100px 100px; */
`;

const StyledInput = styled.input`
  /* Hides the default radio button */
  appearance: none;
  -webkit-appearance: none;
  -moz-appearance: none;

  /* Size and shape of custom radio button */
  width: 30px;
  height: 30px;
  border-radius: 50%;
  cursor: pointer;

  /* Styling of background and border when unchecked */
  background-color: #fff;
  border: 2px solid rgb(200, 200, 200);
  position: relative;

  /* Styling of background and border when checked */
  &:checked {
    background-color: rgb(255, 255, 255);
    border-color: var(--primary-color);
  }

  /* Adding the circle in the middle when checked */
  &:checked::before {
    content: "";
    position: absolute;
    top: 2px;
    left: 2px;
    width: 22px;
    height: 22px;
    background-color: var(--primary-color);
    border-radius: 50%;
  }
`;
const CandidateContainer = styled.div`
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 10px;
`;
const StyledLabel = styled.label`
  font-size: 18px;
  cursor: pointer;

  /* sibling operator "+" only works because the label directly follows the input in the radiobutton setup */
  input:checked + & {
    font-weight: bold;
  }
`;
