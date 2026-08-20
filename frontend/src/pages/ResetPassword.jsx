import { Code2, LockKeyhole } from "lucide-react";
import { useState } from "react";
import { Link, Navigate, useSearchParams } from "react-router-dom";
import AdminShell from "../components/layout/AdminShell";
import ResetPasswordForm from "../components/admin/ResetPasswordForm";
import Input from "../components/common/Input";
import Button from "../components/common/Button";
import { adminService } from "../services/adminService";
import { useAuth } from "../context/AuthContext";
import { passwordRules } from "../utils/validation";

function TokenReset() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token");
  const [form, setForm] = useState({ password: "", confirm: "" });
  const [done, setDone] = useState(false);
  const [error, setError] = useState("");
  const update = (event) => setForm({ ...form, [event.target.name]: event.target.value });
  const submit = async (event) => {
    event.preventDefault();
    setError("");
    if (!token) return setError("This reset link is invalid.");
    if (!passwordRules(form.password)) return setError("Password must be at least 8 characters with uppercase, lowercase, and a number.");
    if (form.password !== form.confirm) return setError("Passwords do not match.");
    try {
      await adminService.completePasswordReset(token, form.password);
      setDone(true);
    } catch (requestError) {
      setError(requestError.response?.data?.detail || requestError.message);
    }
  };
  return (
    <main className="auth-page">
      <Link className="brand auth-brand" to="/"><span><Code2 size={21} /></span> TCT <b>LAB</b></Link>
      <section className="login-card">
        <div className="login-icon"><LockKeyhole /></div>
        <p className="eyebrow">Account recovery</p>
        <h1>Set new password</h1>
        {done ? <><p>Your password was reset successfully.</p><Link className="forgot" to="/admin/login">Go to login</Link></> : <form onSubmit={submit}>
          <Input label="New password" name="password" type="password" autoComplete="new-password" value={form.password} onChange={update} />
          <Input label="Confirm new password" name="confirm" type="password" autoComplete="new-password" value={form.confirm} onChange={update} />
          {error && <p className="form-error">{error}</p>}
          <Button type="submit">Reset password</Button>
        </form>}
      </section>
    </main>
  );
}

export default function ResetPassword() {
  const [searchParams] = useSearchParams();
  const { currentUser, isAuthenticated } = useAuth();
  if (searchParams.get("token")) return <TokenReset />;
  if (!isAuthenticated) return <Navigate to="/admin/login" replace />;
  return <AuthenticatedReset user={currentUser} />;
}

function AuthenticatedReset({ user }) {
  const [done, setDone] = useState(false);
  const [error, setError] = useState("");
  const submit = async (form) => {
    setError("");
    try {
      await adminService.resetPassword(form, user.id);
      setDone(true);
    } catch (requestError) {
      setError(requestError.response?.data?.detail || requestError.message);
    }
  };
  return <AdminShell title="Reset Password"><section className="form-page"><div><p className="eyebrow">Account security</p><h2>Update your password</h2><p>Use a unique password you do not reuse elsewhere.</p></div><div className="form-card">{done ? <div className="success-message"><h3>Password updated</h3><p>Your new hashed password is active immediately.</p></div> : <><ResetPasswordForm onSubmit={submit} />{error && <p className="form-error">{error}</p>}</>}</div></section></AdminShell>;
}
