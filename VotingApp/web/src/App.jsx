import { BrowserRouter as Router, Route, Routes } from "react-router-dom";
import Welcome from "./Screens/Welcome";
import MyPage from "./Screens/MyPage";
import VoteCheck from "./Screens/VoteCheck";
import CandidateSelection from "./Screens/CandidateSelection";
import MemorableInformation from "./Screens/MemorableInformation";
import Confirmation from "./Screens/Confirmation";
import LoginPage from "./Screens/Login";
import PreviousVotes from "./Screens/PreviousVotes";
import { useState, useEffect } from "react";
import { AppProvider } from "./Components/AppContext";

function App() {
  const [electionId, setElectionId] = useState(0);
  const [message, setMessage] = useState("");

  useEffect(() => {
    fetch("/api/election") // /api/ proxy defined in nginx.conf to be http://va_api:8000 (docker address)
      .then((res) => res.json())
      .then((data) => {
        setElectionId(data.electionId);
      })
      .catch((err) => console.error("Error fetching election id:", err));
  }, []);

  useEffect(() => {
    fetch("/api/bulletin/hello") // How do we want to route? We should probably find a pattern/structure we can repeat throughout.
      .then((res) => res.json())
      .then((data) => setMessage(data.message))
      .catch((err) => console.error("Error fetching hello:", err));
  }, []);

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
      <AppProvider>
        <Router>
          {message && <div style={{ padding: 8 }}>{message}</div>}
          <Routes>
            <Route path="/" element={<LoginPage />} />
            <Route path="/Mypage" element={<MyPage />} />
            <Route
              path=":electionId/*"
              element={
                <Routes>
                  <Route path="Welcome" element={<Welcome />} />
                  <Route path="VoteCheck" element={<VoteCheck />} />
                  <Route
                    path="CandidateSelection"
                    element={<CandidateSelection candidates={candidates} />}
                  />
                  <Route
                    path="MemorableInformation"
                    element={<MemorableInformation />}
                  />
                  <Route path="Confirmation" element={<Confirmation />} />
                  <Route path="PreviousVotes" element={<PreviousVotes />} />
                </Routes>
              }
            />
          </Routes>
        </Router>
      </AppProvider>
    )
  );
}

export default App;
