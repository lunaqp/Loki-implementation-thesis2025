import { createContext, useContext, useState, useEffect } from "react";

const AppContext = createContext();

export const AppProvider = ({ children }) => {
  // Saving voter_id as user in local storage.
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem("user");
    return saved ? JSON.parse(saved) : null;
  });

  // Storing election id along with election name in local storage.
  // Example: [{id: 123, name: "Student Council President", "start": XX:YY, "end": XX:YY}]
  const [elections, setElections] = useState(() => {
    const saved = localStorage.getItem("elections");
    return saved ? JSON.parse(saved) : [];
  });

  const [previousVotes, setPreviousVotes] = useState(() => {
    const saved = localStorage.getItem("previousVotes");
    return saved ? JSON.parse(saved) : [];
  });

  const [imageFilename, setImageFilename] = useState(() => {
    const saved = localStorage.getItem("imageFilename");
    return saved ? JSON.parse(saved) : null;
  });

  const [electionName, setElectionName] = useState(() => {
    const saved = localStorage.getItem("electionName");
    return saved ? JSON.parse(saved) : null;
  });

  const [hasUnread, setHasUnread] = useState(true);

  const [timeout, setTimeout] = useState(() => {
    const saved = localStorage.getItem("timeout");
    return saved ? JSON.parse(saved) : {};
  });

  useEffect(() => {
    localStorage.setItem("timeout", JSON.stringify(timeout));
  }, [timeout]);

  // helper: start a timeout for an election
  const startTimeout = (electionId, ms) => {
    const nextEligibleAt = new Date(Date.now() + ms).toISOString();
    setTimeout((prev) => ({ ...prev, [electionId]: nextEligibleAt }));
  };

  // helper to read remaining time
  const getRemainingMs = (electionId) => {
    const iso = timeout[electionId];
    if (!iso) return 0;
    const diff = new Date(iso).getTime() - Date.now();
    return Math.max(0, diff);
  };

  useEffect(() => {
    if (user) localStorage.setItem("user", JSON.stringify(user));
    else localStorage.removeItem("user");
  }, [user]);

  useEffect(() => {
    localStorage.setItem("elections", JSON.stringify(elections));
  }, [elections]);

  useEffect(() => {
    localStorage.setItem("previousVotes", JSON.stringify(previousVotes));
  }, [previousVotes]);

  useEffect(() => {
    localStorage.setItem("imageFilename", JSON.stringify(imageFilename));
  }, [imageFilename]);

  useEffect(() => {
    localStorage.setItem("electionName", JSON.stringify(electionName));
  }, [electionName]);

  // Clearing all user data
  const clearSession = () => {
    setUser(null);
    setElections([]);
    setPreviousVotes([]);
    setImageFilename(null);
    localStorage.clear();
  };

  const clearFlow = () => {
    setPreviousVotes([]);
    setImageFilename(null);
    setElectionName(null);
  };

  return (
    <AppContext.Provider
      value={{
        user,
        setUser,
        elections,
        setElections,
        previousVotes,
        setPreviousVotes,
        imageFilename,
        setImageFilename,
        electionName,
        setElectionName,
        clearSession,
        clearFlow,
        hasUnread,
        setHasUnread,
        timeout,
        startTimeout,
        getRemainingMs,
      }}
    >
      {children}
    </AppContext.Provider>
  );
};

export const useApp = () => useContext(AppContext);
