import React, { useMemo, useState, useCallback } from "react";
import styled from "styled-components";
import { useParams } from "react-router-dom";
import PageTemplate from "../Components/PageTemplate";
import ScreenTemplate from "../Components/ScreenTemplate";
import PVTimeline from "../Components/PVTimeline";
import PVImageDisplay from "../Components/PVImageDisplay";
import ImagesSelected from "../Components/ImagesSelected";

const PreviousVotes = () => {
  const { electionId } = useParams();
  const nextRoute = `/${electionId}/CandidateSelection`;
  const prevRoute = `/${electionId}/VoteCheck`;

  // build image URLs from public/images/<hour>/<index>.jpg
  // set how many images each hour has = 12 (We should adjust/remake this)
  const countsPerHour = useMemo(() => {
    const base = 40;
    const obj = {};
    for (let i = 0; i < 24; i++) obj[String(i).padStart(2, "0")] = base; //keys "00".."23"
    return obj;
  }, []);

  // const base = import.meta.env.BASE_URL || "/";

  //map hour to array of img urls
  const imagesByHour = useMemo(() => {
    const map = {};
    Object.entries(countsPerHour).forEach(([hour, count]) => {
      map[hour] = Array.from(
        { length: count },
        (_, i) => `/images/${hour}/${i + 1}.jpg`
      );
    });
    return map; // { "00": ["/images/00/1.jpg", ...], ... }
  }, [countsPerHour]);

  const [activeHour, setActiveHour] = useState("00"); //state for current active hour
  const [selected, setSelected] = useState([]); //selected imgs/urls
  const [jumpToken, setJumpToken] = useState(0); //incremented on timeline click, triggers scroll

  //handle radiobutton change, set active hour and increment jumptoken
  const handleTimelineChange = useCallback((h) => {
    setActiveHour(h);
    // bump token so PVImageDisplay knows this change came from a radio click
    setJumpToken((n) => n + 1);
  }, []);

  //toggle img selected/unselected
  const toggleSelect = useCallback((src) => {
    setSelected((s) =>
      s.includes(src) ? s.filter((x) => x !== src) : [...s, src]
    );
  }, []);

  return (
    <PageTemplate progress={3} adjustableHeight>
      <ScreenTemplate
        nextRoute={nextRoute}
        prevRoute={prevRoute}
        adjustableHeight
        buttonUnselectable={selected.length === 0}
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
