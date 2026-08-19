import { useState } from "react";
import { useNavigate } from "react-router-dom";
import AdminShell from "../components/layout/AdminShell";
import AddLinkForm from "../components/admin/AddLinkForm";
import { useAuth } from "../context/AuthContext";
import { linkService } from "../services/linkService";
export default function AddLink() {
  const { currentUser } = useAuth();
  const navigate = useNavigate();
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const submit = async (form) => {
    setSaving(true);
    setError("");
    try {
      await linkService.createLink({ ...form, labId: currentUser.labId });
      navigate("/admin/manage-links");
    } catch (requestError) {
      setError(
        requestError.response?.data?.detail ||
          "Link could not be added. Please log in again and retry.",
      );
    } finally {
      setSaving(false);
    }
  };
  return (
    <AdminShell title="Add Link">
      <section className="form-page">
        <div>
          <p className="eyebrow">New resource</p>
          <h2>Add a link to your lab</h2>
          <p>
            Students in <b>{currentUser.labName}</b> will be the only ones to
            see it.
          </p>
        </div>
        <div className="form-card">
          <AddLinkForm onSubmit={submit} />
          {error && <p className="form-error">{error}</p>}
          {saving && <p className="saving-note">Saving link…</p>}
        </div>
      </section>
    </AdminShell>
  );
}
