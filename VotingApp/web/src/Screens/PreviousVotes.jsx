import { useMemo, useState, useCallback, useEffect } from "react";
import styled from "styled-components";
import { useParams, useNavigate } from "react-router-dom";
import PageTemplate from "../Components/PageTemplate";
import ScreenTemplate from "../Components/ScreenTemplate";
import PVTimeline from "../Components/PVTimeline";
import PVImageDisplay from "../Components/PVImageDisplay";
import ImagesSelected from "../Components/ImagesSelected";
import { useApp } from "../Components/AppContext";

const PreviousVotes = () => {
  const { electionId } = useParams();
  const nextRoute = `/${electionId}/CandidateSelection`;
  const prevRoute = `/${electionId}/VoteCheck`;
  const { user, setPreviousVotes } = useApp();
  const navigate = useNavigate();

  const [fetchedImages, setFetchedImages] = useState([]);
  const [activeHour, setActiveHour] = useState("00"); // state for current active hour
  const [selected, setSelected] = useState([]); // selected cbrimages (including index, image, and timestamp)
  const [jumpToken, setJumpToken] = useState(0); // incremented on timeline click, triggers scroll
  const fetchVoterCBR = async (electionId, voterId) => {
    try {
      const response = await fetch(
        `/api/fetch-cbr-images-for-voter?election_id=${electionId}&voter_id=${voterId}`
      );

      if (!response.ok) {
        const errText = await response.text();
        throw new Error(`Error fetching cbr images: ${errText}`);
      }

      const data = await response.json();
      console.log(data.cbrimages);

      return data.cbrimages;
    } catch (error) {
      console.error("Error fetching cbr images:", error);
      throw error;
    }
  };

  useEffect(() => {
    const voterId = user.user;
    const fetchcbr = async () => {
      try {
        const imgs = await fetchVoterCBR(electionId, voterId);
        setFetchedImages(imgs);
      } catch (err) {
        console.log(err.message);
      }
    };
    fetchcbr();
  }, [user]);

  const imagesByHour = useMemo(() => {
    const map = {};

    for (const img of fetchedImages) {
      const date = new Date(img.timestamp);
      const hour = String(date.getHours() + 1).padStart(2, "0"); // date.getHours() +1 to match Copenhagen wintertime
      if (!map[hour]) map[hour] = [];
      map[hour].push({
        index: img.cbrindex,
        image: img.image,
        timestamp: img.timestamp,
      });
    }
    console.log(map);
    return map;
  }, [fetchedImages]);

  //handle radiobutton change, set active hour and increment jumptoken
  const handleTimelineChange = useCallback((h) => {
    setActiveHour(h);
    // bump token so PVImageDisplay knows this change came from a radio click
    setJumpToken((n) => n + 1);
  }, []);

  //toggle img selected/unselected
  const toggleSelect = useCallback((cbrimages) => {
    setSelected((prev) => {
      const exists = prev.some((x) => x.cbrindex === cbrimages.cbrindex);
      if (exists) {
        return prev.filter((x) => x.cbrindex !== cbrimages.cbrindex);
      } else {
        return [...prev, cbrimages];
      }
    });
  }, []);

  const savePreviousVotes = useCallback(() => {
    const selectedIndices = selected.map((img) => img.cbrindex);
    setPreviousVotes(selectedIndices);
    console.log(selectedIndices);

    if (nextRoute) {
      navigate(nextRoute);
    }
  }, [selected]);

  return (
    <PageTemplate progress={3} adjustableHeight>
      <ScreenTemplate
        nextRoute={nextRoute}
        prevRoute={prevRoute}
        adjustableHeight
        buttonUnselectable={selected.length === 0}
        onPrimaryClick={savePreviousVotes}
      >
        <Wrap>
          <Top>
            <Title>Previous Votes</Title>
            <Directions>
              For each vote you cast previously, pick the image you were shown
              afterward. Use the <b>hour timeline</b> below to jump, or scroll
              the gallery. Images are grouped by hour; click an image to select
              it.
            </Directions>
          </Top>

          <Timeline>
            <Title2>Election timeline</Title2>
            <PVTimeline
              activeHour={activeHour}
              onChange={handleTimelineChange}
            />
          </Timeline>

          <ImgGallery>
            <PVImageDisplay
              imagesByHour={imagesByHour}
              selected={selected}
              onToggleSelect={toggleSelect}
              activeHour={activeHour}
              onActiveHourChange={setActiveHour}
              jumpToken={jumpToken}
            />
          </ImgGallery>

          <SelectedImgs>
            <SectionTitle>Selected images</SectionTitle>
            <ImagesSelected images={selected} onRemove={toggleSelect} />
          </SelectedImgs>
        </Wrap>
      </ScreenTemplate>
    </PageTemplate>
  );
};

export default PreviousVotes;

const Wrap = styled.div`
  display: flex;
  flex-direction: column;
  gap: 18px;
  width: 100%;
`;

const Top = styled.div`
  width: 100%;
  padding-bottom: 30px;
`;

const Title = styled.h1`
  margin: 0 0 8px 0;
`;

const Title2 = styled.h2`
  margin: 0 0 8px 0;
`;

const Directions = styled.p`
  margin: 0;
  max-width: 1000px;
`;

const Timeline = styled.div`
  width: 100%;
`;

const ImgGallery = styled.div`
  width: 100%;
`;

const SelectedImgs = styled.div`
  width: 100%;
  padding-bottom: 50px;
`;

const SectionTitle = styled.h3`
  margin: 6px 0 10px 0;
`;
