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

  const [hasUnread, setHasUnread] = useState(true);

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

  // Clearing all user data
  const clearSession = () => {
    setUser(null);
    setElections([]);
    setPreviousVotes([]);
    setImageFilename(null);
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
        imageFilename,
        setImageFilename,
        clearSession,
        hasUnread,
        setHasUnread,
      }}
    >
      {children}
    </AppContext.Provider>
  );
};

export const useApp = () => useContext(AppContext);
