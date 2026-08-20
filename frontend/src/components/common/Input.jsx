import { Eye, EyeOff } from "lucide-react";
import { useState } from "react";

export default function Input({ label, error, id, ...props }) {
  const fieldId = id || props.name;
  const isPassword = props.type === "password";
  const [visible, setVisible] = useState(false);

  return (
    <label className="field" htmlFor={fieldId}>
      <span>{label}</span>
      <span className={isPassword ? "field__input-wrap" : undefined}>
        <input
          id={fieldId}
          aria-invalid={Boolean(error)}
          {...props}
          type={isPassword && visible ? "text" : props.type}
        />
        {isPassword && (
          <button
            className="field__toggle"
            type="button"
            aria-label={visible ? "Hide password" : "Show password"}
            onClick={() => setVisible(!visible)}
          >
            {visible ? <EyeOff size={16} /> : <Eye size={16} />}
          </button>
        )}
      </span>
      {error && <small className="field__error">{error}</small>}
    </label>
  );
}
