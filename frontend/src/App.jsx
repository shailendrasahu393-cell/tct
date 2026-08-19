import { Routes, Route } from "react-router-dom";
import Home from "./pages/Home";
import About from "./pages/About";
import Lab from "./pages/Lab";
import AdminLogin from "./pages/AdminLogin";
import AdminDashboard from "./pages/AdminDashboard";
import AddLink from "./pages/AddLink";
import ManageLinks from "./pages/ManageLinks";
import AddAdmin from "./pages/AddAdmin";
import ResetPassword from "./pages/ResetPassword";
import Unauthorized from "./pages/Unauthorized";
import NotFound from "./pages/NotFound";
import ProtectedRoute from "./routes/ProtectedRoute";
const protect = (Page) => (
  <ProtectedRoute>
    <Page />
  </ProtectedRoute>
);
export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/about" element={<About />} />
      <Route path="/lab/:labId" element={<Lab />} />
      <Route path="/admin/login" element={<AdminLogin />} />
      <Route path="/admin/dashboard" element={protect(AdminDashboard)} />
      <Route path="/admin/add-link" element={protect(AddLink)} />
      <Route path="/admin/manage-links" element={protect(ManageLinks)} />
      <Route
        path="/admin/add-admin"
        element={
          <ProtectedRoute roles={["SUPER_ADMIN"]}>
            <AddAdmin />
          </ProtectedRoute>
        }
      />
      <Route path="/admin/reset-password" element={protect(ResetPassword)} />
      <Route path="/unauthorized" element={<Unauthorized />} />
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
}
