import { useState } from "react";
import AdminShell from "../components/layout/AdminShell";
import AddAdminForm from "../components/admin/AddAdminForm";
import { adminService } from "../services/adminService";
export default function AddAdmin() {
  const [done, setDone] = useState(false);
  const [error, setError] = useState("");
  const submit = async (form) => {
    setError("");
    try {
      await adminService.createAdmin(form);
      setDone(true);
    } catch (requestError) {
      setError(requestError.response?.data?.detail || requestError.message);
    }
  };
  return (
    <AdminShell title="Add Admin">
      <section className="form-page">
        <div>
          <p className="eyebrow">Super admin only</p>
          <h2>Create an admin & lab</h2>
          <p>
            Vivek Sir's account is the only account allowed to create admins.
          </p>
        </div>
        <div className="form-card">
          {done ? (
            <div className="success-message">
              <h3>Admin created successfully</h3>
              <p>
                The new admin can log in immediately with the submitted user ID
                and password.
              </p>
            </div>
          ) : (
            <>
              <AddAdminForm onSubmit={submit} />
              {error && <p className="form-error">{error}</p>}
              <p className="form-help">
                Password rules: minimum 8 characters, with one uppercase letter,
                one lowercase letter, and one number.
              </p>
            </>
          )}
        </div>
      </section>
    </AdminShell>
  );
}
