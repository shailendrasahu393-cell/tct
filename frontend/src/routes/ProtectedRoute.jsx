import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import LoadingSpinner from "../components/common/LoadingSpinner";
export default function ProtectedRoute({ children, roles }) {
  const { isAuthenticated, currentUser, loading } = useAuth();
  const location = useLocation();
  if (loading) return <LoadingSpinner label="Checking your session..." />;
  if (!isAuthenticated)
    return <Navigate to="/admin/login" state={{ from: location }} replace />;
  if (roles && !roles.includes(currentUser.role))
    return <Navigate to="/unauthorized" replace />;
  return children;
}
