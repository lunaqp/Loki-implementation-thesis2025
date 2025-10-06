import React, { useMemo } from "react";
import styled from "styled-components";

//Timeline component, 24 hours
const PVTimeline = ({ activeHour, onChange }) => {
  const hours = useMemo(() => Array.from({ length: 24 }, (_, i) => i), []); //builds array from 0 to 24 once and uses memo to memorize it
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
