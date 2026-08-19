import { useState } from "react";
import Input from "../common/Input";
import Button from "../common/Button";
import { passwordError, passwordRules } from "../../utils/validation";
export default function AddAdminForm({ onSubmit }) {
  const [form, setForm] = useState({
    name: "",
    email: "",
    password: "",
    confirm: "",
    lab: "",
    section: "",
  });
  const [error, setError] = useState("");
  const update = (e) => setForm({ ...form, [e.target.name]: e.target.value });
  const submit = (e) => {
    e.preventDefault();
    if (Object.values(form).some((value) => !value))
      return setError("Please complete all required fields.");
    if (!passwordRules(form.password))
      return setError(passwordError(form.password));
    if (form.password !== form.confirm)
      return setError("Passwords do not match.");
    onSubmit(form);
  };
  return (
    <form className="content-form" onSubmit={submit}>
      <Input
        label="Admin name"
        name="name"
        value={form.name}
        onChange={update}
      />
      <Input
        label="Email or username"
        name="email"
        value={form.email}
        onChange={update}
      />
      <div className="form-row">
        <Input label="Lab name" name="lab" value={form.lab} onChange={update} />
        <Input
          label="Class / section"
          name="section"
          value={form.section}
          onChange={update}
        />
      </div>
      <Input
        label="Temporary password"
        name="password"
        type="password"
        value={form.password}
        onChange={update}
      />
      <Input
        label="Confirm password"
        name="confirm"
        type="password"
        value={form.confirm}
        onChange={update}
      />
      {error && <p className="form-error">{error}</p>}
      <Button>Create admin</Button>
    </form>
  );
}
