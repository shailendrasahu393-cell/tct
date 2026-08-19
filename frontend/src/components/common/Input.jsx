export default function Input({ label, error, id, ...props }) {
  const fieldId = id || props.name;
  return (
    <label className="field" htmlFor={fieldId}>
      <span>{label}</span>
      <input id={fieldId} aria-invalid={Boolean(error)} {...props} />
      {error && <small className="field__error">{error}</small>}
    </label>
  );
}
