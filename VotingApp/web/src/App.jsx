import { BrowserRouter as Router, Route, Routes } from "react-router-dom";
import Welcome from "./Screens/Welcome";
import MyPage from "./Screens/MyPage";
import VoteCheck from "./Screens/VoteCheck";
import CandidateSelection from "./Screens/CandidateSelection";
import MemorableInformation from "./Screens/MemorableInformation";
import Confirmation from "./Screens/Confirmation";
import LoginPage from "./Screens/Login";
import PreviousVotes from "./Screens/PreviousVotes";
import { AppProvider } from "./Components/AppContext";
import Instructions from "./Screens/Instructions";

function App() {
  return (
    <AppProvider>
      <Router>
        <Routes>
          <Route path="/" element={<LoginPage />} />
          <Route path="/Mypage" element={<MyPage />} />
          <Route path="/instructions" element={<Instructions />} />

          <Route
            path=":electionId/*"
            element={
              <Routes>
                <Route path="Welcome" element={<Welcome />} />
                <Route path="VoteCheck" element={<VoteCheck />} />
                <Route
                  path="CandidateSelection"
                  element={<CandidateSelection />}
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
  );
}

export default App;
