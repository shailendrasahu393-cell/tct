import {
  LayoutDashboard,
  PlusCircle,
  List,
  UserPlus,
  KeyRound,
  LogOut,
  X,
} from "lucide-react";
import { NavLink } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
const entries = [
  { to: "/admin/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/admin/add-link", label: "Add Link", icon: PlusCircle },
  { to: "/admin/manage-links", label: "Manage Links", icon: List },
  { to: "/admin/reset-password", label: "Reset Password", icon: KeyRound },
];
export default function AdminSidebar({ open, onClose }) {
  const { currentUser, logout } = useAuth();
  return (
    <aside className={`sidebar ${open ? "sidebar--open" : ""}`}>
      <button className="icon-button sidebar__close" onClick={onClose}>
        <X />
      </button>
      <div className="sidebar__brand">
        TCT <b>LAB</b>
        <small>ADMIN PANEL</small>
      </div>
      <nav>
        {entries.map(({ to, label, icon: Icon }) => (
          <NavLink key={to} to={to} onClick={onClose}>
            <Icon size={18} />
            {label}
          </NavLink>
        ))}
        {currentUser?.role === "SUPER_ADMIN" && (
          <NavLink to="/admin/add-admin" onClick={onClose}>
            <UserPlus size={18} />
            Add Admin
          </NavLink>
        )}
      </nav>
      <button className="sidebar__logout" onClick={logout}>
        <LogOut size={18} />
        Logout
      </button>
    </aside>
  );
}
