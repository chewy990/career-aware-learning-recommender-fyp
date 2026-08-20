import { useEffect, useRef } from "react";

/**
 * Confirm a destructive action inside the app.
 *
 * Native dialogs are unavailable in sandboxed frames, where window.confirm
 * returns false and the action silently does nothing. This keeps confirmation
 * under the product's own control.
 */
export default function ConfirmDialog({ request, onClose }) {
  const confirmRef = useRef(null);

  useEffect(() => {
    if (!request) return undefined;
    confirmRef.current?.focus();
    function onKeyDown(event) {
      if (event.key === "Escape") onClose();
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [request, onClose]);

  if (!request) return null;

  function confirm() {
    onClose();
    request.onConfirm();
  }

  return (
    <div className="confirm-backdrop" onClick={onClose} role="presentation">
      <div
        className="confirm-dialog"
        role="alertdialog"
        aria-modal="true"
        aria-labelledby="confirm-title"
        aria-describedby="confirm-message"
        onClick={(event) => event.stopPropagation()}
      >
        <h2 id="confirm-title">{request.title}</h2>
        <p id="confirm-message">{request.message}</p>
        <div className="confirm-actions">
          <button type="button" className="confirm-cancel" onClick={onClose}>
            Cancel
          </button>
          <button
            type="button"
            className="confirm-accept"
            ref={confirmRef}
            onClick={confirm}
          >
            {request.confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
