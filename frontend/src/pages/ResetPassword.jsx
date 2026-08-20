import { useState } from "react";
import AdminShell from "../components/layout/AdminShell";
import ResetPasswordForm from "../components/admin/ResetPasswordForm";
import { adminService } from "../services/adminService";
import { useAuth } from "../context/AuthContext";

export default function ResetPassword() {
  const { currentUser } = useAuth();
  const [done, setDone] = useState(false);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const submit = async (form) => {
    if (saving) return;
    setError("");
    setSaving(true);
    try {
      await adminService.resetPassword(form, currentUser.id);
      setDone(true);
    } catch (requestError) {
      setError(requestError.response?.data?.detail || requestError.message);
    } finally {
      setSaving(false);
    }
  };
  return (
    <AdminShell title="Change Password">
      <section className="form-page">
        <div>
          <p className="eyebrow">Account security</p>
          <h2>Update your password</h2>
          <p>Use your current password to set a new password.</p>
        </div>
        <div className="form-card">
          {done ? (
            <div className="success-message">
              <h3>Password updated</h3>
              <p>Your new hashed password is active immediately.</p>
            </div>
          ) : (
            <>
              <ResetPasswordForm onSubmit={submit} submitting={saving} />
              {error && <p className="form-error">{error}</p>}
            </>
          )}
        </div>
      </section>
    </AdminShell>
  );
}
