import React, { useEffect, useMemo, useRef } from "react";
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

  const hours = useMemo(() => Object.keys(imagesByHour).sort(), [imagesByHour]); //sorted list of hour keys

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
                  const isSelected = selected.some((x) => x.cbrindex === index);
                  return (
                    <Clickableimg
                      key={index}
                      $active={isSelected}
                      onClick={() =>
                        onToggleSelect({ cbrindex: index, image, timestamp })
                      }
                      title={isSelected ? "Deselect" : "Select"}
                      type="button"
                    >
                      <Img
                        src={`/images/${image}.png`}
                        alt={`${image}`}
                        loading="lazy"
                      />
                    </Clickableimg>
                  );
                })}
              </Grid>
              {idx < hours.length - 1 && <Divider />}{" "}
              {/*separater between sections*/}
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
  grid-template-columns: repeat(8, minmax(0, 1fr));
  gap: 10px;
  padding: 12px 2px 8px;
`;

const Clickableimg = styled.button`
  border: 2px solid
    ${({ $active }) =>
      $active ? "var(--primary-color,#2563eb)" : "rgba(0,0,0,0.15)"};
  border-radius: 10px;
  padding: 0;
  background: #fff;
  cursor: pointer;
  outline: none;

  &:hover {
    border-color: var(--primary-color, #2563eb);
  }
`;

const Img = styled.img`
  display: block;
  width: 100%;
  height: 110px;
  object-fit: contain;
  border-radius: 8px;
`;

const Divider = styled.div`
  height: 18px;
  border-bottom: 2px dashed rgba(0, 0, 0, 0.2);
  margin: 6px 0 14px 0;
`;
