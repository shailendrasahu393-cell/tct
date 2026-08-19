import { ShieldCheck } from "lucide-react";
import { useState } from "react";
import { useAuth } from "../../context/AuthContext";
import AdminSidebar from "./AdminSidebar";
export default function AdminShell({ title, children, action }) {
  const [open, setOpen] = useState(false);
  const { currentUser } = useAuth();
  return (
    <div className="admin-shell">
      <AdminSidebar open={open} onClose={() => setOpen(false)} />
      <main className="admin-main">
        <header className="admin-header">
          <div>
            <p>Administration</p>
            <h1>{title}</h1>
          </div>
          {action}
          <div className="profile">
            <span>
              <ShieldCheck size={17} />
            </span>
            <div>
              <b>{currentUser?.name}</b>
              <small>{currentUser?.role?.replace("_", " ")}</small>
            </div>
          </div>
        </header>
        {children}
      </main>
    </div>
  );
}
