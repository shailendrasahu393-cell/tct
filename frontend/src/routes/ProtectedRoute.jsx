import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
export default function ProtectedRoute({ children, roles }) {
  const { isAuthenticated, currentUser } = useAuth();
  const location = useLocation();
  if (!isAuthenticated)
    return <Navigate to="/admin/login" state={{ from: location }} replace />;
  if (roles && !roles.includes(currentUser.role))
    return <Navigate to="/unauthorized" replace />;
  return children;
}
