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

  //   const [choices, setChoices] = useState(() => {
  //     const saved = localStorage.getItem("choices");
  //     return saved ? JSON.parse(saved) : {};
  //   });

  // Persist to localStorage
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

  //   useEffect(() => {
  //     localStorage.setItem("choices", JSON.stringify(choices));
  //   }, [choices]);

  //   // Utility: update a single choice
  //   const updateChoice = (electionId, candidateId) => {
  //     setChoices(prev => ({ ...prev, [electionId]: candidateId }));
  //   };

  // Utility: clear all user data (on logout)
  const clearSession = () => {
    setUser(null);
    setElections([]);
    // setChoices({});
    localStorage.clear();
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
        //   choices, setChoices,
        //   updateChoice,
        clearSession,
      }}
    >
      {children}
    </AppContext.Provider>
  );
};

export const useApp = () => useContext(AppContext);
