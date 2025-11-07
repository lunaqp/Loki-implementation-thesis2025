import React, { useEffect, useMemo, useRef, useState } from "react";
import styled from "styled-components";

// TODO: change createRef usage to match modern React.

//renders scrollable gallery of imgs
//keeps timeline (radios) in sync both when you scroll and when you click
const PVImageDisplay = ({
  imagesByHour, //Mapping of CBR index to image filename to timestamp
  selected, //array of selected imgs
  onToggleSelect,
  activeHour, // current hour active
  onActiveHourChange, // tell parent when scroll makes a new hour active
  jumpToken, // increments when user clicks a radio
}) => {
  const wrapRef = useRef(null); //ref to iner scroller container
  const sectionRefs = useRef({}); //ref the hour to the section element
  const markerRefs = useRef({}); //ref marker element above header
  const programmaticScroll = useRef(false); //true while scrolling, flase when clicking buttons
  const cooldownUntil = useRef(0); //after scrolling we cooldown before switching to programmaticScroll=false
  const [isImageZoomed, setIsImageZoomed] = useState(false);
  const hours = useMemo(() => Object.keys(imagesByHour).sort(), [imagesByHour]); //sorted list of hour keys
  const [zoomedImage, setZoomedImage] = useState();

  const onZoomClick = (image) => {
    setIsImageZoomed(true);
    setZoomedImage(image);
  };

  const handleCloseModal = () => {
    setIsImageZoomed(false);
    setZoomedImage(null);
  };

  //Handle radio click, scroll into view when jumpToken changes
  useEffect(() => {
    if (!jumpToken) return;
    //find section key for active hour
    const key = activeHour;
    const target = sectionRefs.current[key]?.current;
    const root = wrapRef.current;
    if (!target || !root) return;

    //start scrolling to picked hour
    programmaticScroll.current = true;
    cooldownUntil.current = Date.now() + 300;

    // Scroll only the inner container not page
    const rootRect = root.getBoundingClientRect();
    const targetRect = target.getBoundingClientRect();
    // align target/section to the top of the container (like block: 'start')
    const top = targetRect.top - rootRect.top + root.scrollTop - 15; //-15 is a small margin between imgs and hourlabel
    root.scrollTo({ top, behavior: "smooth" });

    //Flip programmatic scroll to false.
    const id = setTimeout(() => {
      programmaticScroll.current = false;
    }, 300);
    return () => clearTimeout(id);
  }, [jumpToken, activeHour]);

  //Scroll gallery, update activeHour
  useEffect(() => {
    const root = wrapRef.current;
    if (!root) return;

    const observers = [];
    //observe marker
    hours.forEach((h) => {
      if (!markerRefs.current[h]) markerRefs.current[h] = React.createRef();
      const el = markerRefs.current[h].current;
      if (!el) return;

      const obs = new IntersectionObserver(
        (entries) => {
          //ignore observer event while programmatic scrolling
          if (programmaticScroll.current || Date.now() < cooldownUntil.current)
            return;

          // When a marker is reasonably visible in our favored zone, set that hour as active (updates the radios).
          for (const e of entries) {
            if (e.isIntersecting && e.intersectionRatio >= 0.2) {
              if (h !== activeHour) onActiveHourChange(h);
              break;
            }
          }
        },
        {
          root,
          //favor markers near the upper half of the view
          rootMargin: "-30% 0px -60% 0px",
          threshold: [0.01, 0.25, 0.5],
        }
      );
      obs.observe(el);
      observers.push(obs);
    });

    //disconnect all observers on unmount
    return () => observers.forEach((o) => o.disconnect());
  }, [hours, activeHour, onActiveHourChange]);

  return (
    //scrollable container
    <Frame>
      <Wrap ref={wrapRef}>
        {hours.map((h, idx) => {
          //create refs for each hour section + marker
          if (!sectionRefs.current[h])
            sectionRefs.current[h] = React.createRef();
          if (!markerRefs.current[h]) markerRefs.current[h] = React.createRef();

          const hourLabel = `${h}-${String((Number(h) + 1) % 24).padStart(
            2,
            "0"
          )}`;
          const imgs = imagesByHour[h] || [];

          return (
            //one section per hour, used by radiobuttons
            <Section key={h} ref={sectionRefs.current[h]}>
              <Marker ref={markerRefs.current[h]} />
              <HourHeader>{hourLabel}</HourHeader>
              {/*grid of imgs for this hour*/}
              <Grid>
                {imgs.map(({ index, image, timestamp }) => {
                  // generating word from image filename. For example "hockey_stick_11s.jpg".
                  const imagetext = image
                    .replace(/^./, (c) => c.toUpperCase()) // -> Hockey_stick_11s.jpg
                    .slice(0, -8) // -> hockey_stick
                    .replaceAll("_", " ") // -> hockey stick
                    .replace(/\d+$/, ""); // removing ekstra digit. For example in bow1, bow2, and bow3.
                  const isSelected = selected.some((x) => x.cbrindex === index);
                  return (
                    <TextImageBox>
                      <ImageText>{imagetext}</ImageText>
                      <ImageMagnifyBox>
                        <Clickableimg
                          key={index}
                          $active={isSelected}
                          onClick={() =>
                            onToggleSelect({
                              cbrindex: index,
                              image,
                              timestamp,
                            })
                          }
                          title={isSelected ? "Deselect" : "Select"}
                          type="button"
                        >
                          <Img
                            src={`/images/${image}`}
                            alt={`${image}`}
                            loading="lazy"
                          />
                        </Clickableimg>
                        <ZoomButton onClick={() => onZoomClick(image)}>
                          <img
                            src="/magnifying-glass-solid-full.svg" // FontAwesome icon - https://fontawesome.com/icons/magnifying-glass?f=classic&s=solid
                            alt="Zoom"
                          />
                        </ZoomButton>
                      </ImageMagnifyBox>
                    </TextImageBox>
                  );
                })}
              </Grid>
              {/*separater between sections*/}
              {idx < hours.length - 1 && <Divider />}{" "}
              {/*Pop-up for zoomed images*/}
              {isImageZoomed && (
                <ImagePopUp onClick={handleCloseModal}>
                  {/*In combination with the ImagePopUp onClick, this closes the image when clicking anywhere but the ImagePopUp. */}
                  <ImagePopUpContainer onClick={(e) => e.stopPropagation()}>
                    <CloseX onClick={handleCloseModal}>×</CloseX>
                    <ZoomedImage
                      src={`/images/${zoomedImage}`}
                      alt={`${zoomedImage}`}
                    />
                  </ImagePopUpContainer>
                </ImagePopUp>
              )}{" "}
            </Section>
          );
        })}
      </Wrap>
    </Frame>
  );
};

export default PVImageDisplay;

const Frame = styled.div`
  width: 100%;
  border: 2px solid #000;
  border-radius: 20px;
  overflow: hidden;
  background: #fff;
  box-sizing: border-box;
`;

const PADDING = 15;

const Wrap = styled.div`
  width: 100%;
  height: 600px;
  overflow: auto;
  overscroll-behavior: contain;
  padding: ${PADDING}px;
  box-sizing: border-box;

  // Firefox
  scrollbar-width: thin;
  scrollbar-color: rgba(0, 0, 0, 0.35) transparent;

  // WebKit (Chrome/Edge/Safari)
  &::-webkit-scrollbar {
    width: 10px;
  }
  &::-webkit-scrollbar-track {
    background: transparent;
    margin: 12px 0;
  }
  &::-webkit-scrollbar-thumb {
    background: rgba(0, 0, 0, 0.35);
    border-radius: 9999px;
  }
`;

const Section = styled.section`
  scroll-margin-top: 6px;
`;

const Marker = styled.div`
  height: 1px;
  margin-top: -1px;
`;

const HourHeader = styled.div`
  position: sticky;
  top: -${PADDING}px;
  background: #fff;
  padding: ${4 + PADDING}px 6px 4px 6px;
  font-weight: 700;
  border-bottom: 1px solid rgba(0, 0, 0, 0.15);
  z-index: 1;
`;

const Grid = styled.div`
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  gap: 10px;
  padding: 12px 2px 8px;
`;

const Clickableimg = styled.button`
  border: 2px solid
    ${({ $active }) => ($active ? "var(--primary-color)" : "rgba(0,0,0,0.15)")};
  border-radius: 10px;
  padding: 0;
  background: #fff;
  cursor: pointer;
  outline: none;

  &:hover {
    border-color: var(--primary-color);
  }
`;

const Img = styled.img`
  display: block;
  width: 100%;
  height: 134px;
  object-fit: contain;
  border-radius: 8px;
`;

const Divider = styled.div`
  height: 18px;
  border-bottom: 2px dashed rgba(0, 0, 0, 0.2);
  margin: 6px 0 14px 0;
`;

const TextImageBox = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  border-radius: 10px;
  background-color: #f2f2f2;
`;

const ImageText = styled.p`
  line-height: 0;
  font-size: 9;
`;

const ImageMagnifyBox = styled.div`
  position: relative;
  display: inline-block;
`;

const ZoomButton = styled.button`
  position: absolute;
  bottom: 4px;
  right: 2px;
  background: rgba(233, 233, 233, 0.9);
  border: none;
  border-radius: 8px 0 8px 0;
  padding: 7px;
  cursor: pointer;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);

  &:hover {
    background: var(--primary-color);
    color: white;
  }

  img {
    width: 14px;
    height: 14px;
    display: block;
  }
`;

const ImagePopUp = styled.div`
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background-color: rgba(0, 0, 0, 0.7);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  z-index: 10;
`;

const ImagePopUpContainer = styled.div`
  position: relative;
  background-color: #f5f5f5;
  padding: 30px;
  border-radius: 10px 10px 10px 10px;
`;

const ZoomedImage = styled.img`
  width: 600px;
  height: auto;
`;

const CloseX = styled.button`
  position: absolute;
  top: 0px;
  right: 4px;
  border: 0;
  background: transparent;
  font-size: 24px;
  line-height: 1;
  cursor: pointer;
  color: #64748b;
  padding: 5px 5px;
  &:hover {
    color: #111827;
  }
`;
