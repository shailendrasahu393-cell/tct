import { Code2, LockKeyhole } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router-dom";
import Input from "../components/common/Input";
import Button from "../components/common/Button";
import { adminService } from "../services/adminService";

export default function ForgotPassword() {
  const [identity, setIdentity] = useState("");
  const [sent, setSent] = useState(false);
  const [error, setError] = useState("");
  const submit = async (event) => {
    event.preventDefault();
    setError("");
    if (!identity.trim()) return setError("Enter your username or recovery email.");
    try {
      await adminService.requestPasswordReset(identity);
      setSent(true);
    } catch (requestError) {
      setError(requestError.response?.data?.detail || requestError.message);
    }
  };
  return (
    <main className="auth-page">
      <Link className="brand auth-brand" to="/">
        <span><Code2 size={21} /></span> TCT <b>LAB</b>
      </Link>
      <section className="login-card">
        <div className="login-icon"><LockKeyhole /></div>
        <p className="eyebrow">Account recovery</p>
        <h1>Forgot password?</h1>
        {sent ? (
          <p>A reset link has been sent if the account exists. Check your email.</p>
        ) : (
          <>
            <p>Enter your username or recovery email to receive a reset link.</p>
            <form onSubmit={submit}>
              <Input
                label="Username or recovery email"
                name="identity"
                autoComplete="username"
                value={identity}
                onChange={(event) => setIdentity(event.target.value)}
              />
              {error && <p className="form-error">{error}</p>}
              <Button type="submit">Send reset link</Button>
            </form>
          </>
        )}
        <Link className="forgot" to="/admin/login">Back to login</Link>
      </section>
    </main>
  );
}
