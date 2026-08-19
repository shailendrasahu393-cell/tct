export default function ErrorMessage({
  title = "Something went wrong.",
  onRetry,
}) {
  return (
    <div className="message message--error">
      <strong>{title}</strong>
      <p>Please try again.</p>
      {onRetry && <button onClick={onRetry}>Retry</button>}
    </div>
  );
}
