import { useState } from "react";
import Button from "../common/Button";
import Input from "../common/Input";
import { isValidUrl } from "../../utils/validation";
export default function AddLinkForm({ onSubmit, initialValue, submitting = false }) {
  const [form, setForm] = useState(
    initialValue || {
      category: "Daily Lab",
      title: "",
      description: "",
      url: "",
      date: new Date().toISOString().slice(0, 10),
    },
  );
  const [errors, setErrors] = useState({});
  const update = (e) => setForm({ ...form, [e.target.name]: e.target.value });
  const submit = (e) => {
    e.preventDefault();
    const next = {};
    if (!form.title.trim()) next.title = "Title is required.";
    if (!form.url) next.url = "URL is required.";
    else if (!isValidUrl(form.url))
      next.url = "Enter a valid URL including https://.";
    if (!form.category) next.category = "Select a category.";
    setErrors(next);
    if (!Object.keys(next).length && !submitting) onSubmit(form);
  };
  return (
    <form className="content-form" onSubmit={submit}>
      <label className="field">
        <span>Link type</span>
        <select name="category" value={form.category} onChange={update}>
          <option>Contest</option>
          <option>Daily Lab</option>
          <option>Single Problem</option>
        </select>
        {errors.category && (
          <small className="field__error">{errors.category}</small>
        )}
      </label>
      <Input
        label="Title"
        name="title"
        placeholder="e.g. Day 05 — Strings"
        value={form.title}
        onChange={update}
        error={errors.title}
      />
      <label className="field">
        <span>
          Description <small>(optional)</small>
        </span>
        <textarea
          name="description"
          placeholder="A short description for students"
          value={form.description}
          onChange={update}
          rows="4"
        />
      </label>
      <Input
        label="Problem URL"
        name="url"
        type="url"
        placeholder="https://..."
        value={form.url}
        onChange={update}
        error={errors.url}
      />
      <Input
        label="Date"
        name="date"
        type="date"
        value={form.date}
        onChange={update}
      />
      <Button type="submit" disabled={submitting}>
        {submitting ? "Saving..." : initialValue ? "Save changes" : "Add link"}
      </Button>
    </form>
  );
}
