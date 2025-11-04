import { useMemo, useEffect, useState } from "react";
import styled from "styled-components";

//Timeline component, 24 hours
const PVTimeline = ({ activeHour, onChange, electionId }) => {
  const [startdate, setStartdate] = useState();
  const [enddate, setEnddate] = useState();

  // Fetch election start and enddate
  const fetchElectionDates = async (electionId) => {
    try {
      const response = await fetch(
        `/api/fetch-election-dates?election_id=${electionId}`
      );

      if (!response.ok) {
        const errText = await response.text();
        throw new Error(`Error fetching electiondates: ${errText}`);
      }

      // Response has structure: {"startdate": DATE, "enddate": DATE}
      const dates = await response.json();
      console.log("election start and end date:", dates);
      setStartdate(dates.startdate);
      setEnddate(dates.enddate);
    } catch (error) {
      console.error("Error fetching electiondates:", error);
      throw error;
    }
  };

  useEffect(() => {
    const fetchdates = async () => {
      try {
        await fetchElectionDates(electionId);
      } catch (err) {
        console.log(err.message);
      }
    };
    fetchdates();
  }, []);

  // ONLY WORKS FOR SAME DAY ELECTIONS. TODO: Rework if we want to support elections spanning multiple days.
  // Creating an array of all hour-intervals in the election for populating the timeline with data.
  const hours = useMemo(() => {
    const startHour = new Date(startdate).getHours();
    const endHour = new Date(enddate).getHours();
    const hoursToShow = endHour - startHour + 1;
    const intervalArray = [];
    for (let index = 0; index < hoursToShow; index++) {
      intervalArray.push(startHour + index);
    }

    return intervalArray;
  }, [startdate, enddate]);

  //reder labels 00-01 wraps at 24
  const label = (h) =>
    `${String(h).padStart(2, "0")}-${String((h + 1) % 24).padStart(2, "0")}`;

  return (
    <Bar>
      {hours.map((h) => {
        //map each hour to clickable button
        const key = String(h).padStart(2, "0"); //two digit "00".."23"
        const isActive = key === activeHour;
        return (
          <Item
            key={key}
            type="button"
            onClick={() => onChange(key)}
            aria-pressed={isActive} // pressed state for toggle buttons
            title={`Jump to ${label(h)}`}
          >
            <Radio $active={isActive} aria-hidden />
            <Txt $active={isActive}>{label(h)}</Txt>{" "}
            {/*timeline text, bold when selected */}
          </Item>
        );
      })}
    </Bar>
  );
};

export default PVTimeline;

const Bar = styled.div`
  display: grid;
  grid-template-columns: repeat(12, minmax(0, 1fr)); //12 per row
  gap: 12px 18px;
  align-items: center;
  padding: 10px 12px;
  border: 1px solid rgba(0, 0, 0, 0.15);
  border-radius: 10px;
  background: #fff;
  white-space: nowrap;
  width: 100%;
`;

const Item = styled.button`
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 4px 6px;
  border: none;
  background: transparent;
  cursor: pointer;
`;

const Radio = styled.span`
  width: 16px;
  height: 16px;
  border: 2px solid
    ${({ $active }) =>
      $active ? "var(--primary-color,#2563eb)" : "rgba(0,0,0,0.45)"};
  border-radius: 50%;
  position: relative;

  &::after {
    content: "";
    position: absolute;
    inset: 3px;
    border-radius: 50%;
    background: ${({ $active }) =>
      $active ? "var(--primary-color,#2563eb)" : "transparent"};
  }
`;

const Txt = styled.span`
  font-weight: ${({ $active }) => ($active ? 700 : 500)};
`;
