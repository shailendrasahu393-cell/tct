import { Trash2 } from "lucide-react";
import { useEffect, useState } from "react";
import AdminShell from "../components/layout/AdminShell";
import LoadingSpinner from "../components/common/LoadingSpinner";
import { labService } from "../services/labService";

export default function ManageLabs() {
  const [labs, setLabs] = useState(null);
  const [error, setError] = useState("");

  const load = async () => {
    try {
      setLabs(await labService.getLabs());
    } catch (requestError) {
      setError(requestError.response?.data?.detail || requestError.message);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const remove = async (lab) => {
    if (!window.confirm(`Delete ${lab.name}? Its links and assigned admin will also be deleted.`)) return;
    setError("");
    try {
      await labService.deleteLab(lab.id);
      setLabs((currentLabs) => currentLabs.filter((item) => item.id !== lab.id));
    } catch (requestError) {
      setError(requestError.response?.data?.detail || requestError.message);
    }
  };

  return (
    <AdminShell title="Manage Labs">
      <section className="dashboard-content">
        <div className="page-heading">
          <p className="eyebrow">Admin database access</p>
          <h2>Manage labs</h2>
          <p>Labs are saved in the backend database. Deleting a lab also removes its links and assigned admin.</p>
        </div>
        {error && <p className="form-error">{error}</p>}
        {!labs ? (
          <LoadingSpinner label="Loading labs..." />
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr><th>Lab</th><th>Class</th><th>Assigned faculty</th><th aria-label="Actions" /></tr>
              </thead>
              <tbody>
                {labs.map((lab) => (
                  <tr key={lab.id}>
                    <td><b>{lab.name}</b><small>{lab.id}</small></td>
                    <td>{lab.className}</td>
                    <td>{lab.facultyName}</td>
                    <td>
                      <button className="icon-button danger" title="Delete lab" onClick={() => remove(lab)} disabled={lab.id === "lab-001"}>
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