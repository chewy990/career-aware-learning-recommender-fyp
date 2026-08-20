import { useState } from "react";
import { CheckCircle2, KeyRound } from "lucide-react";
import { PASSWORD_MIN_LENGTH, PasswordInput } from "./AuthStep";

export default function PasswordStep({ onSubmit, onBack }) {
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmedPassword, setConfirmedPassword] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    if (!currentPassword || !newPassword || !confirmedPassword) {
      setError("Complete all three password fields.");
      return;
    }
    if (newPassword.length < PASSWORD_MIN_LENGTH) {
      setError(`Use at least ${PASSWORD_MIN_LENGTH} characters for the new password.`);
      return;
    }
    if (newPassword !== confirmedPassword) {
      setError("The new passwords do not match.");
      return;
    }
    if (currentPassword === newPassword) {
      setError("Choose a new password that is different from the current one.");
      return;
    }

    try {
      setSubmitting(true);
      setError("");
      setSuccess("");
      await onSubmit({
        current_password: currentPassword,
        new_password: newPassword,
      });
      setCurrentPassword("");
      setNewPassword("");
      setConfirmedPassword("");
      setSuccess("Password updated. Other signed-in sessions have been closed.");
    } catch (err) {
      setError(err.message || "Could not update the password.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="account-security-page">
      <section className="auth-panel account-security-panel">
        <div className="section-heading auth-heading">
          <span>Account security</span>
          <h2>Change your password</h2>
          <p>Confirm your current password, then choose a new passphrase for this account.</p>
        </div>

        <form className="auth-form" onSubmit={handleSubmit}>
          <PasswordInput
            id="current-password"
            label="Current password"
            value={currentPassword}
            autoComplete="current-password"
            invalid={Boolean(error)}
            onChange={setCurrentPassword}
          />
          <PasswordInput
            id="new-password"
            label="New password"
            value={newPassword}
            autoComplete="new-password"
            describedBy="new-password-help"
            invalid={Boolean(error)}
            onChange={setNewPassword}
          />
          <small id="new-password-help" className="password-help">
            Use at least {PASSWORD_MIN_LENGTH} characters. A memorable passphrase works well.
          </small>
          <PasswordInput
            id="confirm-password"
            label="Confirm new password"
            value={confirmedPassword}
            autoComplete="new-password"
            invalid={Boolean(error)}
            onChange={setConfirmedPassword}
          />

          {error && <div className="error-banner" role="alert" aria-live="polite">{error}</div>}
          {success && (
            <div className="success-banner" role="status">
              <CheckCircle2 aria-hidden="true" />
              {success}
            </div>
          )}

          <div className="auth-actions">
            <button className="primary" type="submit" disabled={submitting}>
              <KeyRound aria-hidden="true" />
              {submitting ? "Updating password..." : "Update password"}
            </button>
            <button className="ghost" type="button" onClick={onBack}>Back to courses</button>
          </div>
        </form>
      </section>
    </div>
  );
}
