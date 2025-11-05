import styled from "styled-components";
import { useNavigate } from "react-router-dom";
import { useState } from "react";

const InstructionsPage = () => {
  const nav = useNavigate();
  return (
    <Page>
      <BodyContainer>
        <Container>
          <PageTitle>Instructions</PageTitle>
          <PageIntro>
            Here you can find a step by step guide of how to use the voting
            system, aswell as Frequently Asked Questions.
          </PageIntro>

          {/* Instructions */}
          <Card accent="blue">
            <SectionHeader>How to cast a vote</SectionHeader>
            <StepList>
              <li>
                1. Open your election and press <b>Vote</b>.
              </li>
              <li>2. Make your selection and confirm.</li>
              <li>3. Verify your vote in the app if needed.</li>
              <li>4. Verify your vote in the app if needed.</li>
              <li>
                5. Verify your vote in the app if needed . Verify your vote in
                the app if needed Verify your vote in the app if needed Verify
                your vote in the app if needed
              </li>
            </StepList>
          </Card>

          {/* FAQ */}
          <Card accent="slate">
            <SectionHeader>FAQ</SectionHeader>
            <FAQItem q="Can I verify my vote?">
              You can verify inclusion via the <b>Verify</b> button on MyPage.
            </FAQItem>
            <FAQItem q="Is my vote private?">
              Yes. Your ballot is encrypted and anonymized before submission.
            </FAQItem>
            <FAQItem q="What if I lose connection while voting?">
              Reopen the app and retry. If you’re unsure, use <b>Verify</b>.
            </FAQItem>
          </Card>
          <ButtonBar>
            <BackButton onClick={() => nav("/Mypage")}>
              Back to MyPage
            </BackButton>
          </ButtonBar>
        </Container>
      </BodyContainer>
    </Page>
  );
};

function FAQItem({ q, children }) {
  const [open, setOpen] = useState(false);
  return (
    <FAQBox $open={open}>
      <FAQQuestion onClick={() => setOpen((v) => !v)} aria-expanded={open}>
        <span>{q}</span>
        <i>{open ? "–" : "+"}</i>
      </FAQQuestion>
      {open && <FAQAnswer>{children}</FAQAnswer>}
    </FAQBox>
  );
}

export default InstructionsPage;

const Page = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  min-height: 100vh;
  width: 100%;
  overflow: hidden;
`;

const BodyContainer = styled.div`
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: flex-start;
  width: 1080px;
  height: auto;
  gap: 20px;
  border: 1px solid black;
  border-radius: 20px;
  background-color: var(--secondary-color);
  padding: 20px 60px 10px 60px;
  margin-top: 30px;
  margin-bottom: 30px;
`;

const ButtonBar = styled.div`
  position: sticky;
  top: 0;
  z-index: 3;
  display: flex;
  justify-content: flex-start;
`;

const BackButton = styled.button`
  padding: 10px 20px;
  border: none;
  border-radius: 8px;
  background: rgb(50, 50, 50);
  color: white;
  font-weight: 600;
  cursor: pointer;
  margin-top: 20px;

  &:hover {
    background-color: rgb(225, 225, 225);
    color: black;
    border-color: rgb(50, 50, 50);
  }
`;

const Container = styled.main`
  width: 900px;
  margin: 25px auto 50px;
  padding: 0 24px;
`;

const PageTitle = styled.h1`
  font-size: clamp(28px, 4vw, 42px);
  line-height: 1.15;
  margin: 8px 0 8px;
`;

const PageIntro = styled.p`
  color: #4b5563;
  font-size: 1.06rem;
  margin: 0 0 30px;
`;

const Card = styled.section`
  border: 1px solid rgb(50, 50, 50);
  border-left: 6px solid rgb(50, 50, 50);
  border-radius: 14px;
  padding: 24px 24px 24px;
  margin: 18px 0 28px;
`;

const SectionHeader = styled.h2`
  font-size: 1.5rem;
  margin: 0 0 14px;
`;

const StepList = styled.ol`
  margin: 0;
  padding-left: 0;
  list-style: none;
  li + li {
    margin-top: 10px;
  }

  li {
    border: 1px solid #e5e7eb;
    border-radius: 10px;
    padding: 14px 16px;
    text-align: left;
    background: #fff;
  }
`;

const FAQBox = styled.div`
  border-radius: 10px;
  border: 1px solid #e5e7eb;
  background: #fff;
  margin: 10px 0;
  overflow: hidden;
  transition: border-color 0.2s;
  ${({ $open }) => $open && `border-color: var(--primary);`}
`;

const FAQQuestion = styled.button`
  width: 100%;
  text-align: left;
  padding: 14px 16px;
  background: transparent;
  border: 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 700;
  cursor: pointer;

  i {
    font-style: normal;
    font-size: 20px;
    line-height: 0;
    color: rgb(50, 50, 50);
  }
  &:hover {
    background: #f8fafc;
  }
  &:focus-visible {
    outline: 2px solid var(--primary);
    outline-offset: 2px;
  }
`;

const FAQAnswer = styled.div`
  padding: 0 16px 14px;
  color: black;
  line-height: 1.6;
`;
