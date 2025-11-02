import { createContext, useState, useContext } from "react";

const ElectionContext = createContext();

export const ElectionManager = ({ children }) => {
  const [previousVotes, setPreviousVotes] = useState(null);
  const [chosenCandidate, setChosenCandidate] = useState(null);

  const value = {
    previousVotes,
    setPreviousVotes,
    chosenCandidate,
    setChosenCandidate,
  };

  return (
    <ElectionContext.Provider value={value}>
      {children}
    </ElectionContext.Provider>
  );
};

export const useElection = () => useContext(ElectionContext);
