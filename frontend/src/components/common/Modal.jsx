import { X } from "lucide-react";
export default function Modal({ title, children, onClose }) {
  return (
    <div className="modal-backdrop" role="presentation">
      <section
        className="modal"
        role="dialog"
        aria-modal="true"
        aria-label={title}
        style={{ maxHeight: "calc(100vh - 40px)", overflowY: "auto" }}
      >
        <button
          className="icon-button modal__close"
          onClick={onClose}
          aria-label="Close dialog"
        >
          <X size={20} />
        </button>
        <h2>{title}</h2>
        {children}
      </section>
    </div>
  );
}
