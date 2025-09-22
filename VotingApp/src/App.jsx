import { BrowserRouter as Router, Route, Routes } from "react-router-dom";
import Welcome from "./Screens/Welcome";
import FrontPage from "./Screens/FrontPage";
import VoteCheck from "./Screens/VoteCheck";
import CandidateSelection from "./Screens/CandidateSelection";
import MemorableInformation from "./Screens/MemorableInformation";
import Confirmation from "./Screens/Confirmation";
import { useState, useEffect } from "react";

function App() {
  const [electionId, setElectionId] = useState(0);
  const [elections, setElections] = useState([]);
  const [message, setMessage] = useState("");

  useEffect(() => {
    fetch("/api/election")
      .then((res) => res.json())
      .then((data) => {
        setElectionId(data.electionId);
      });
  }, []);

  useEffect(() => {
    fetch("/api/elections")
      .then((res) => res.json())
      .then((data) => {
        const mapped = data.elections.map((e) => ({
          id: e.electionId,
          name: e.electionName,
          // Candidates
        }));
        setElections(mapped);
      });
  }, []);

  useEffect(() => {
    fetch("/api/bulletin/hello") // How do we want to route? We should probably find a pattern/structure we can repeat throughout.
      .then((res) => res.json())
      .then((data) => setMessage(data.message))
      .catch((err) => console.error("Error fetching hello:", err));
  }, []);

  console.log(elections);

  // Fetching candidates from BB for later use (passed as prop in candidateseletion).
  // TODO: figure out how to handle this global information that should be available throughout the app without passing around props.
  const [candidates, setCandidates] = useState();

  useEffect(() => {
    fetch("/api/bulletin/candidates")
      .then((res) => res.json())
      .then((data) => {
        setCandidates(data.candidates);
      })
      .catch((err) => console.error("Error fetching candidates:", err));
  }, []);

  return (
    electionId && (
      <Router>
        {message && <div style={{ padding: 8 }}>{message}</div>}
        <Routes>
          <Route path="/" element={<FrontPage electionId={electionId} />} />

          <Route path=":electionId/Welcome" element={<Welcome />} />
          <Route path=":electionId/VoteCheck" element={<VoteCheck />} />
          <Route
            path=":electionId/CandidateSelection"
            element={<CandidateSelection candidates={candidates} />}
          />
          <Route
            path=":electionId/MemorableInformation"
            element={<MemorableInformation />}
          />
          <Route path=":electionId/Confirmation" element={<Confirmation />} />
          {/* <Route path=":electionId/PreviousVotes" element={<PreviousVotes />} />
         
         
        */}
        </Routes>
      </Router>
    )
  );
}

export default App;
