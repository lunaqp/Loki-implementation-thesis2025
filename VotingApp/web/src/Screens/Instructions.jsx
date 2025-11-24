import styled from "styled-components";
import { useNavigate } from "react-router-dom";
import { useState } from "react";

const InstructionsPage = () => {
  const [welcomeExpanded, setWelcomeExpanded] = useState(false);
  const [voteCheckExpanded, setVoteCheckExpanded] = useState(false);
  const [previousVotesExpanded, setPreviousVotesExpanded] = useState(false);
  const [candidatesExpanded, setCandidatesExpanded] = useState(false);
  const [memorableInfoExpanded, setMemorableInfoExpanded] = useState(false);
  const [confirmationExpanded, setConfirmationExpanded] = useState(false);
  const nav = useNavigate();

  const handleClick = (step) => {
    switch (step) {
      case 1:
        if (welcomeExpanded === false) setWelcomeExpanded(true);
        else setWelcomeExpanded(false);
        break;
      case 2:
        if (voteCheckExpanded === false) setVoteCheckExpanded(true);
        else setVoteCheckExpanded(false);
        break;
      case 3:
        if (previousVotesExpanded === false) setPreviousVotesExpanded(true);
        else setPreviousVotesExpanded(false);
        break;
      case 4:
        if (candidatesExpanded === false) setCandidatesExpanded(true);
        else setCandidatesExpanded(false);
        break;
      case 5:
        if (memorableInfoExpanded === false) setMemorableInfoExpanded(true);
        else setMemorableInfoExpanded(false);
        break;
      case 6:
        if (confirmationExpanded === false) setConfirmationExpanded(true);
        else setConfirmationExpanded(false);
        break;
      default:
    }
  };

  return (
    <Page>
      <BodyContainer>
        <Container>
          <PageTitle>Instructions</PageTitle>
          <PageIntro>
            On this page you will find information about system use, background,
            coercion resistance and Frequently Asked Questions.
          </PageIntro>

          {/* Voting process */}
          <Card>
            <SectionHeader>The voting process - Step by step</SectionHeader>
            <StepList>
              <li>
                <b>Step 1: Welcome </b>
                <br />
                This is the first screen you will see when clicking "Vote" in an
                election. This screen welcomes you to the voting process.
                <br />
                <ImageContainer>
                  <ImageButton onClick={() => handleClick(1)}>
                    {welcomeExpanded ? "- Hide image" : "+ Expand image"}
                  </ImageButton>
                  {welcomeExpanded && (
                    <Image
                      src={"/screenshots/welcome.png"}
                      alt="Welcome step"
                    />
                  )}
                </ImageContainer>
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
                <br />
                <ImageContainer>
                  <ImageButton onClick={() => handleClick(2)}>
                    {voteCheckExpanded ? "- Hide image" : "+ Expand image"}
                  </ImageButton>
                  {voteCheckExpanded && (
                    <Image
                      src={"/screenshots/Votecheck.png"}
                      alt="Vote Check step"
                    />
                  )}
                </ImageContainer>
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
                <ImageContainer>
                  <ImageButton onClick={() => handleClick(3)}>
                    {previousVotesExpanded ? "- Hide image" : "+ Expand image"}
                  </ImageButton>
                  {previousVotesExpanded && (
                    <Image
                      src={"/screenshots/PreviousVotes.png"}
                      alt="Previous Votes Step"
                    />
                  )}
                </ImageContainer>
              </li>

              <li>
                <b>Step 3 - NO: Select a candidate to vote for</b>
                <br />
                In this step you will choose the candidate to vote for in the
                given election.
                <br />
                Make sure you are voting for the intended candidate before you
                move on.
                <br />
                <ImageContainer>
                  <ImageButton onClick={() => handleClick(4)}>
                    {candidatesExpanded ? "- Hide image" : "+ Expand image"}
                  </ImageButton>
                  {candidatesExpanded && (
                    <Image
                      src={"/screenshots/CandidateSelection.png"}
                      alt="Candidate Selection Step"
                    />
                  )}
                </ImageContainer>
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
                <br />
                <ImageContainer>
                  <ImageButton onClick={() => handleClick(5)}>
                    {memorableInfoExpanded ? "- Hide image" : "+ Expand image"}
                  </ImageButton>
                  {memorableInfoExpanded && (
                    <Image
                      src={"/screenshots/MemorableInformation.png"}
                      alt="Memorable Information Step"
                    />
                  )}
                </ImageContainer>
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
                You will have the option to wait for the system to verify that
                your vote is included in the election. In case there is an error
                or the vote is not included, you will need to cast a new vote
                with your intended candidate choice. We recommend you cast the
                new vote from a different device.
                <br />
                <br />
                <RedText>
                  After you have completed the voting process, there will be a
                  timeout of 6 minutes to ensure the systems security mechanisms
                  work as intended. Be aware that a coercer will know that you
                  have voted before if they see that you are on timeout.
                </RedText>
                <br />
                <ImageContainer>
                  <ImageButton onClick={() => handleClick(6)}>
                    {confirmationExpanded ? "- Hide image" : "+ Expand image"}
                  </ImageButton>
                  {confirmationExpanded && (
                    <Image
                      src={"/screenshots/Confirmation.png"}
                      alt="Confirmation Step"
                    />
                  )}
                </ImageContainer>
              </li>
            </StepList>
          </Card>

          {/* FAQ */}
          <Card>
            <SectionHeader>FAQ</SectionHeader>
            <FAQItem q="What does coercion mean?">
              Coercion, in this context, refers to a situation where someone
              tries to force or pressure you into voting for a specific
              candidate, often in exchange for a reward, under threat, or due to
              social/personal pressure.
              <br />
              <br />
              In short, coercion means your vote is not truly free or private,
              because another person is trying to control your choice in an
              election.
            </FAQItem>
            <FAQItem q="Why do we need coercion resistance in electronic voting systems? ?">
              When introducing electronic or remote voting, it comes with a
              number of important advantages, such as greater accessibility,
              convenience, and faster election processing.
              <br />
              <br />
              However, remote voting also introduces new challenges. Unlike
              traditional polling stations, remote environments are not
              controlled, which means voters may be more vulnerable to coercion
              attempts.
              <br />
              <br />
              That's why coercion resistance is essential in electronic voting
              systems. It ensures that even if someone tries to coerce a voter,
              the system is designed so that:
              <br />
              - The voter can safely mislead a coercer without revealing their
              true choice.
              <br />
              - Only the voter's final, genuine vote is counted.
              <br />
              - No one can prove how they voted, protecting them from threats or
              manipulation.
              <br />
              <br />
              In short, coercion resistance protects both the integrity of the
              election and the free choice of the voter.
            </FAQItem>
            <FAQItem q="How does Loki Coercion resistance work?">
              Loki is designed so that you can{" "}
              <b>appear to follow a coercer's instructions</b>, while the system
              still protects your real vote.
              <br />
              <br />
              It does this using three main ideas:
              <br />
              <br />
              <b>1. You can vote multiple times</b>
              <br />
              You are allowed to cast several votes in the same election. In the
              final count, only <b>one</b> vote per person will be included.
              This makes it possible to:
              <br />
              - Cast a “fake” vote under pressure, and
              <br />
              - Later cast a new, genuine vote when you are safe.
              <br />
              <br />
              <b>2. Each vote gets a secret image/word</b>
              <br />
              After each vote, you see a unique image/word pair. Only you know
              which images belong to your real votes. When you later say you
              have voted before (Step 3 - YES), you must identify all images
              from all your previous votes, real and fake. This proves that{" "}
              <b>you</b> are the same person changing your vote.
              <br />
              <br />
              <b>3. The system can silently invalidate coerced votes</b>
              <br />
              The system internally checks whether your behaviour matches what a
              genuine voter would do:
              <br />- If you have already voted but select “NO” in Step 2, the
              system will still let you go through the steps, but will secretly
              mark this new vote as invalid.
              <br />- If you select “YES” but provide one or more{" "}
              <b>wrong images</b>, the system again allows you to finish, but
              will invalidate that vote.
              <br />
              <br />
              In both situations a coercer will only see that you have voted
              “correctly”, while Loki makes sure that only your final, genuine
              vote is counted in the election.
            </FAQItem>
            <FAQItem q="What if I am coerced after I have already cast a vote with my true candidate choice?">
              If you have already submitted a vote for your intended candidate
              before being coerced, don't worry.
              <br />
              <br />
              In this situation, you can safely pretend to comply with the
              coercer:
              <br />
              - In Step 2, select “NO”. The system will recognize that you have
              already voted and secretly mark this new, coerced vote as invalid.
              <br />
              - Alternatively, if you select “YES” in Step 2, you can choose an
              incorrect image. The system will again detect this and secretly
              invalidate the coerced vote.
              <br />
              <br />
              In both cases, your original, genuine vote remains valid, and the
              coerced one will not be counted.
            </FAQItem>
            <FAQItem q="What if I am coerced before I have managed to cast a vote my true candidate choice?">
              Don't panic, you're still protected.
              <br />
              <br />
              If you're forced to vote by a coercer before you can make your
              real choice:
              <br />
              - Complete the coerced vote as instructed and memorize the image
              that appears with it.
              <br />
              - Later, when you are alone, you can revote for your true
              candidate by entering that same image in “Step 3 - YES”.
              <br />
              <br />
              This ensures that your final vote reflects your real choice.
            </FAQItem>
            <FAQItem q="Do I need to remember all the images from my previous votes, or just the last one if I revoted multiple times?">
              If you have revoted multiple times, you must remember all the
              images from your previous votes.
              <br />
              When you revote, you'll need to provide every image from your
              earlier votes in order to submit a valid new vote.
            </FAQItem>
            <FAQItem q="Why is there a timeout after I have voted?">
              The timeout exists for security and anti-coercion reasons. It
              helps ensure that the system's coercion resistant mechanisms work
              properly and prevents a coercer from repeatedly forcing you to
              vote.
              <br />
              <br />
              It also limits the number of votes you can cast in a short period,
              which helps you remember your images more easily when revoting
              later. Be aware that if a coercer sees that you are on timeout,
              they may realize you've already voted.
            </FAQItem>
            <FAQItem q="How can I verify my vote is correctly cast?">
              The system will automatically verify that your vote is properly
              included in the election. You can wait for this process at the
              last screen of the voting process.
              <br />
              For security reasons, you will not be able to directly confirm
              which candidate you voted for. This ensures that your vote remains
              confidential and coercion resistant.
            </FAQItem>
            <FAQItem q="What do I do if the verification of my vote fails?">
              If your vote cannot be succesfully verified you should cast a new
              vote. We recommend that you do this from a different device.
              <br />
              The image associated with the invalid vote will no longer matter
              and you can forget about it. Just make sure to remember the new
              image displayed when you cast your new, valid vote.
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

const ImageButton = styled.button`
  display: inline-flex;
  align-items: center;
  width: fit-content;
  gap: 6px;
  font-size: 14px;
  color: var(--primary-color);
  background: var(--secondary-color);
  border: 1px solid rgba(114, 152, 183, 0.4);
  border-radius: 6px;
  padding: 4px 10px;
  cursor: pointer;
  transition: all 0.2s ease;
  margin: 5px 0 5px 0;

  &:hover {
    background: var(--primary-color);
    color: white;
    border-color: var(--primary-color);
  }
`;

const ImageContainer = styled.div`
  display: flex;
  flex-direction: column;
`;

const Image = styled.img`
  width: 100%;
  height: auto;
  border-radius: 10px;
`;
