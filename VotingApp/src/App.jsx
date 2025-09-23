import { BrowserRouter as Router, Route, Routes } from "react-router-dom";
import Welcome from "./Screens/Welcome";
import MyPage from "./Screens/MyPage";
import VoteCheck from "./Screens/VoteCheck";
import CandidateSelection from "./Screens/CandidateSelection";
import MemorableInformation from "./Screens/MemorableInformation";
import Confirmation from "./Screens/Confirmation";
import LoginPage from "./Screens/Login";
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
    fetch("/api/bulletin/hello")
      .then((res) => res.json())
      .then((data) => setMessage(data.message))
      .catch((err) => console.error("Error fetching hello:", err));
  }, []);

  console.log(elections);

  return (
    electionId && (
      <Router>
        {message && <div style={{ padding: 8 }}>{message}</div>}
        <Routes>
          <Route path="/" element={<LoginPage />} />

          <Route path="/Mypage" element={<MyPage electionId={electionId} />} />

          <Route path=":electionId/Welcome" element={<Welcome />} />
          <Route path=":electionId/VoteCheck" element={<VoteCheck />} />
          <Route
            path=":electionId/CandidateSelection"
            element={<CandidateSelection />}
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
