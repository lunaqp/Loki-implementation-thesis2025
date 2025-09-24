import { useState } from "react";
import styled from "styled-components";
import { useNavigate } from "react-router-dom";

const LoginPage = () => {
  const navigate = useNavigate();
  const [login, setlogin] = useState({ username: "", password: "" });
  const [error, setError] = useState("");

  const onChange = (e) => {
    const { name, value } = e.target;
    setlogin((f) => ({ ...f, [name]: value }));
  };

  const onSubmit = (e) => {
    e.preventDefault();
    setError("");

    // Replace this with auth.  Checks if both fields are non-empty.
    const ok = login.username.trim() && login.password.trim();
    if (!ok) {
      setError("Please enter both username and password.");
      return;
    }

    navigate("/Mypage");
  };

  return (
    <PageWrapper>
      <LoginBox onSubmit={onSubmit}>
        <h1>Log in</h1>

        <Field>
          <label>Username</label>
          <input
            id="username"
            name="username"
            type="text"
            autoComplete="username"
            value={login.username}
            onChange={onChange}
            placeholder="Enter your username"
            required
          />
        </Field>

        <Field>
          <label>Password</label>
          <input
            id="password"
            name="password"
            type="password"
            autoComplete="current-password"
            value={login.password}
            onChange={onChange}
            placeholder="Enter your password"
            required
          />
        </Field>

        {error && <ErrorMsg>{error}</ErrorMsg>}

        <Button type="submit">Log in</Button>
      </LoginBox>
    </PageWrapper>
  );
};

export default LoginPage;

const PageWrapper = styled.div`
  background-color: white;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
`;

const LoginBox = styled.form`
  width: 420px;
  display: flex;
  flex-direction: column;
  gap: 18px;
  padding: 48px;
  border-radius: 16px;
  background: var(--secondary-color);
  border: 2px solid rgba(0, 0, 0, 0.15);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);

  h1 {
    margin: 0 0 0px;
  }
`;

const Field = styled.div`
  display: flex;
  flex-direction: column;
  gap: 6px;

  label {
    font-weight: 600;
  }
  input {
    height: 40px;
    padding: 0 12px;
    border: 2px solid rgba(0, 0, 0, 0.15);
    border-radius: 10px;
    font-size: 14px;
    outline: none;
  }
  input:focus {
    border-color: var(--primary-color);
  }
`;

const Button = styled.button`
  margin-top: 8px;
  height: 44px;
  border: none;
  border-radius: 10px;
  background: var(--primary-color, #2563eb);
  color: white;
  font-weight: 600;
  cursor: pointer;
`;

const ErrorMsg = styled.div`
  color: #b00020;
  font-size: 14px;
`;
