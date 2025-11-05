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
            On this page you will find information about system use, background,
            coercion resistance and Frequently Asked Questions.
          </PageIntro>

          {/* Instructions */}
          <Card accent="blue">
            <SectionHeader>The voting process - Step by step</SectionHeader>
            <StepList>
              <li>
                <b>Step 1: Welcome </b>
                <br />
                This is the first screen you will see when clicking "Vote" in an
                election. This screen welcomes you to the voting process.
              </li>

              <li>
                <b>Step 2: Have you voted before?</b>
                <br />
                In this step, you will be asked to state if you have already
                voted in this election.
                <br />
                - If this is your first time voting in this election, select
                “No” and you will proceed to select a candidate to vote for.
                <br />
                - If you have already cast one or more previous votes and want
                to change who you voted for, select “Yes”. You will then be
                directed to the previous votes selection screen.
                <br />
                <br />
                <RedText>
                  This step is the first part of the coercion resistant
                  mechanism. If you are being coerced, and have already voted in
                  this election, you can select “No” and the system will
                  automatically know not to count the vote you are about to
                  cast.
                </RedText>
              </li>

              <li>
                <b>Step 3 - YES: Select previous votes </b>
                <br />
                This step will only be shown if you answered “Yes” to having
                voted earlier in this election. This step in combination with
                step 4 are the main function of the coercion resistant
                mechanism.
                <br />
                <br />
                The purpose of this step is to confirm that YOU are the one
                changing your vote and that you are not coerced into doing so.
                <br />
                You will be asked to identify all previously cast votes by
                providing all the image/word-pairs that were displayed after you
                cast your previous vote(s).
                <br />
                - Search through the images of the election period by using the
                timeline or by scrolling through the hours.
                <br />
                - Click the images to select. The selected images will be
                displayed in a list of “selected images” in the bottom. It is
                not necessary that the previous images/words are provided in the
                correct order.
                <br />
                - To unselect images, click them in the “selected images” list
                and they will be deleted from the list.
                <br />
                <br />
                <RedText>
                  It is crucial that you choose the correct image/word pair, as
                  if it is wrong the system will still allow you to cast the
                  vote but will mark the vote as invalid.
                </RedText>
              </li>

              <li>
                <b>Step 3 – NO: Select a candidate to vote for</b>
                <br />
                In this step you will choose the candidate to vote for in the
                given election.
                <br />
                Make sure you are voting for the intended candidate before you
                move on.
              </li>

              <li>
                <b>
                  Step 4: Get the memorable information connected to your vote
                </b>
                <br />
                This step is very important.
                <br />
                You will be shown a new image/word, which you will have to
                remember in case you want to change your vote later. It is
                crucial that you remember this exact image as you will have to
                identify it among a lot of other images if you want to change
                your vote.
                <br />
                <br />
                <RedText>
                  Make sure you have the information memorised before you move
                  on! Once you click “Next” you cannot go back.
                </RedText>
              </li>

              <li>
                <b>Step 5: Confirmation</b>
                <br />
                This is the last step in the voting process.
                <br />
                This is the only confirmation you will see. For security
                reasons, the system will not send you a receipt e-mail to
                confirm your choice of candidate.
                <br />
                <br />
                The system will automatically verify that your vote is included
                in the election. In case there is an error or the vote is not
                included, the system will send you an email, telling you to
                revote.
                <br />
                <br />
                <RedText>
                  After you have completed the voting process, there will be a
                  timeout of 6 minutes to ensure the systems security mechanisms
                  work as intended. Be aware that a coercer will know that you
                  have voted before if they see that you are on timeout.
                </RedText>
              </li>
            </StepList>
          </Card>

          {/* FAQ */}
          <Card accent="slate">
            <SectionHeader>FAQ</SectionHeader>
            <FAQItem q="What does coercion mean?">
              blablablaaaaa............
            </FAQItem>
            <FAQItem q="Why do we need coercion resistance in electronic voting systems? ?">
              blablablaaaaa.............
            </FAQItem>
            <FAQItem q="How does LOKI Coercion resistance work?">
              blablablaaaaa............
            </FAQItem>
            <FAQItem q="Why is there a timeout after I have voted?">
              blablablaaaaa............
            </FAQItem>
            <FAQItem q="How can I verify my vote is correctly cast?">
              blablablaaaaa............
            </FAQItem>
            <FAQItem q="What do I do if I receive an email saying my vote is not included?">
              blablablaaaaa............
            </FAQItem>
            <FAQItem q="What if I forgot my memorable information/image?">
              blablablaaaaa............
            </FAQItem>
            <FAQItem q="Should I only remember the image for the most recent vote I cast or all of the images if i revoted multiple times?">
              blablablaaaaa............
            </FAQItem>
            <FAQItem q="What if I am coerced after I have already cast a vote with my true candidate choice?">
              blablablaaaaa............
            </FAQItem>
            <FAQItem q="What if I am coerced before I have managed to cast a vote my true candidate choice?">
              blablablaaaaa............
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

const RedText = styled.p`
  color: red;
  margin: 0;
`;

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
    margin-top: 15px;
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
