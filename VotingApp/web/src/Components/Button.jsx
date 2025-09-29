import styled, { css } from "styled-components";

/**
 * A button component that renders different styles based on the `variant` prop.
 * It supports a "primary" variant and a "secondary" variant for different button appearances.
 * 
 * @param {Object} props - The props for the button. 
  @param {string} props.variant - The style variant for the button. Can be "primary" or "secondary".
 * @param {function} props.onClick - A callback function to handle the click event.
 * @param {ReactNode} props.children - The content to display inside the button (e.g., text or icons).
 * @returns {JSX.Element} A styled button component based on the `variant` prop.
 */
const Button = ({ variant, onClick, children, unselectable }) => {
  return variant === "primary" ? (
    <PrimaryButton
      onClick={onClick}
      $unselectable={unselectable}
      disabled={unselectable}
    >
      {children}
    </PrimaryButton>
  ) : (
    <SecondaryButton onClick={onClick}>{children}</SecondaryButton>
  );
};

export default Button;

const BaseButton = css`
  padding: 10px 20px;
  border-radius: 8px;
  cursor: pointer;
  height: fit-content;
  width: fit-content;
  text-decoration: none;
  font-size: 16px;
  line-height: 1;
  font-family: inherit;
  font-weight: 500;
  //transition: border-color 0.5s;
  border: solid 2px transparent;
  box-shadow: 0 3px 6px 0 rgba(0, 0, 0, 0.2);
`;
const PrimaryButton = styled.button`
  ${BaseButton}
  color: white;
  background-color: rgb(50, 50, 50);

  &:hover {
    background-color: rgb(225, 225, 225);
    color: black;
    border-color: rgb(50, 50, 50);
  }

  ${({ $unselectable }) =>
    $unselectable &&
    `
    background-color: grey;
    color: white;
    cursor: default;
    opacity: 0.5;

    &:hover {
    background-color: grey;
    color: white;
    border: solid 2px transparent;
  }
  `}
`;
const SecondaryButton = styled.button`
  ${BaseButton}
  color: black;
  background-color: rgb(225, 225, 225);
  border-color: rgb(50, 50, 50);

  &:hover {
    background-color: rgb(50, 50, 50);
    color: white;
    border-color: rgb(50, 50, 50);
  }
`;
