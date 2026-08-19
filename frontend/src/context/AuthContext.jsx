import { createContext, useContext, useEffect, useState } from 'react';
import { authService } from '../services/authService';
const AuthContext = createContext(null);
export function AuthProvider({ children }) {
  const [currentUser, setCurrentUser] = useState(null);
  const [loading, setLoading] = useState(true);
  useEffect(() => { authService.getCurrentUser().then(setCurrentUser).finally(() => setLoading(false)); }, []);
  const login = async (credentials) => { setLoading(true); try { const user = await authService.login(credentials); setCurrentUser(user); return user; } finally { setLoading(false); } };
  const logout = async () => { await authService.logout(); setCurrentUser(null); };
  return <AuthContext.Provider value={{ currentUser, isAuthenticated: Boolean(currentUser), loading, login, logout }}>{children}</AuthContext.Provider>;
}
export const useAuth = () => useContext(AuthContext);
