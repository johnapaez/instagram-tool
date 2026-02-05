import { useState, useEffect } from 'react';
import LoginForm from './components/LoginForm';
import Dashboard from './components/Dashboard';
import type { LoginResponse } from './types';

interface Session {
  sessionId: string;
  username: string;
}

function App() {
  const [session, setSession] = useState<Session | null>(null);

  // Load session from localStorage on mount
  useEffect(() => {
    const savedSession = localStorage.getItem('instagram_session');
    if (savedSession) {
      try {
        const parsed = JSON.parse(savedSession);
        setSession(parsed);
      } catch (err) {
        localStorage.removeItem('instagram_session');
      }
    }
  }, []);

  const handleLogin = (response: LoginResponse) => {
    if (response.success && response.session_id && response.username) {
      const newSession = {
        sessionId: response.session_id,
        username: response.username,
      };
      setSession(newSession);
      localStorage.setItem('instagram_session', JSON.stringify(newSession));
    }
  };

  const handleLogout = () => {
    setSession(null);
    localStorage.removeItem('instagram_session');
  };

  if (!session) {
    return <LoginForm onLogin={handleLogin} />;
  }

  return (
    <Dashboard
      sessionId={session.sessionId}
      username={session.username}
      onLogout={handleLogout}
    />
  );
}

export default App;
