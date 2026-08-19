import { Trash2 } from "lucide-react";
import { useEffect, useState } from "react";
import AdminShell from "../components/layout/AdminShell";
import LoadingSpinner from "../components/common/LoadingSpinner";
import { adminService } from "../services/adminService";

export default function ManageAdmins() {
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  const load = async () => {
    try {
      setResult(await adminService.getAdmins());
    } catch (requestError) {
      setError(requestError.response?.data?.detail || requestError.message);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const remove = async (admin) => {
    if (!window.confirm(`Delete ${admin.name}? Their assigned lab and links will also be deleted.`)) return;
    try {
      await adminService.deleteAdmin(admin.id);
      setResult((current) => ({
        activeAdmins: current.activeAdmins - 1,
        admins: current.admins.filter((item) => item.id !== admin.id),
      }));
    } catch (requestError) {
      setError(requestError.response?.data?.detail || requestError.message);
    }
  };

  return (
    <AdminShell title="Manage Admins">
      <section className="dashboard-content">
        <div className="page-heading">
          <p className="eyebrow">Super admin only</p>
          <h2>Active admins: {result?.activeAdmins ?? "..."}</h2>
          <p>Passwords are never returned or displayed. Remove an admin only when their lab should also be removed.</p>
        </div>
        {error && <p className="form-error">{error}</p>}
        {!result ? <LoadingSpinner label="Loading admins..." /> : (
          <div className="table-wrap">
            <table>
              <thead><tr><th>Name</th><th>User ID</th><th>Role</th><th>Lab</th><th aria-label="Actions" /></tr></thead>
              <tbody>
                {result.admins.map((admin) => (
                  <tr key={admin.id}>
                    <td><b>{admin.name}</b></td>
                    <td>{admin.id}</td>
                    <td>{admin.role}</td>
                    <td>{admin.labId || "-"}</td>
                    <td>
                      <button className="icon-button danger" title="Delete admin" onClick={() => remove(admin)} disabled={admin.role === "SUPER_ADMIN"}>
                        <Trash2 size={16} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </AdminShell>
  );
}