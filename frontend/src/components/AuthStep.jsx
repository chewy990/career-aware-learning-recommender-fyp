import { useState } from "react";
import { Check, Eye, EyeOff } from "lucide-react";

export const PASSWORD_MIN_LENGTH = 12;

export function PasswordInput({
  id,
  label,
  value,
  onChange,
  autoComplete,
  describedBy,
  invalid = false,
}) {
  const [isVisible, setIsVisible] = useState(false);

  return (
    <label className="field" htmlFor={id}>
      <span>{label}</span>
      <div className="password-field">
        <input
          id={id}
          name={id}
          type={isVisible ? "text" : "password"}
          value={value}
          autoComplete={autoComplete}
          maxLength={200}
          required
          aria-describedby={describedBy}
          aria-invalid={invalid}
          onChange={(event) => onChange(event.target.value)}
        />
        <button
          className="password-toggle"
          type="button"
          aria-label={isVisible ? `Hide ${label.toLowerCase()}` : `Show ${label.toLowerCase()}`}
          aria-pressed={isVisible}
          onClick={() => setIsVisible((current) => !current)}
        >
          {isVisible ? <EyeOff aria-hidden="true" /> : <Eye aria-hidden="true" />}
        </button>
      </div>
    </label>
  );
}

export default function AuthStep({ onSubmit, onBack, notice = "" }) {
  const [mode, setMode] = useState("login");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const isRegistering = mode === "register";
  const passwordLongEnough = password.length >= PASSWORD_MIN_LENGTH;

  function changeMode(nextMode) {
    setMode(nextMode);
    setPassword("");
    setError("");
  }

  async function handleSubmit(event) {
    event.preventDefault();
    const nextUsername = username.trim().toLowerCase();
    if (!nextUsername || !password) {
      setError("Enter both a username and password.");
      return;
    }
    if (isRegistering && !/^[a-z0-9][a-z0-9._-]{2,39}$/.test(nextUsername)) {
      setError("Use 3-40 lowercase letters, numbers, dots, hyphens, or underscores.");
      return;
    }
    if (isRegistering && !passwordLongEnough) {
      setError(`Use at least ${PASSWORD_MIN_LENGTH} characters for your password.`);
      return;
    }
    try {
      setSubmitting(true);
      setError("");
      await onSubmit(mode, { username: nextUsername, password });
    } catch (err) {
      setError(err.message || "Could not sign in.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="auth-shell">
      <section className="auth-panel">
        <div className="section-heading auth-heading">
          <h2>{isRegistering ? "Create an account" : "Log in"}</h2>
          <p>
            {isRegistering
              ? "Save your courses and progress."
              : "Continue your saved courses."}
          </p>
        </div>

        {notice && <div className="auth-notice" role="status">{notice}</div>}

        <form className="auth-form" onSubmit={handleSubmit}>
          <label className="field" htmlFor="username">
            <span>Username</span>
            <input
              id="username"
              name="username"
              value={username}
              autoComplete="username"
              autoCapitalize="none"
              spellCheck="false"
              maxLength={80}
              required
              aria-invalid={Boolean(error)}
              onChange={(event) => setUsername(event.target.value)}
            />
            {isRegistering && (
              <small>Lowercase letters, numbers, dots, hyphens, or underscores.</small>
            )}
          </label>

          <PasswordInput
            id="password"
            label="Password"
            value={password}
            autoComplete={isRegistering ? "new-password" : "current-password"}
            describedBy={isRegistering ? "password-requirement" : undefined}
            invalid={Boolean(error)}
            onChange={setPassword}
          />

          {isRegistering && (
            <div
              id="password-requirement"
              className={passwordLongEnough ? "password-requirement met" : "password-requirement"}
            >
              <Check aria-hidden="true" />
              At least {PASSWORD_MIN_LENGTH} characters. Use a password you do not use elsewhere.
            </div>
          )}

          {error && <div className="error-banner" role="alert" aria-live="polite">{error}</div>}

          <div className="auth-actions auth-login-action">
            <button className="primary" type="submit" disabled={submitting}>
              {submitting
                ? isRegistering ? "Creating account..." : "Logging in..."
                : isRegistering ? "Create account" : "Log in"}
            </button>
          </div>
        </form>

        <div className="auth-footer-actions">
          <button
            className="auth-text-action"
            type="button"
            onClick={() => changeMode(isRegistering ? "login" : "register")}
          >
            {isRegistering ? "Already have an account? Log in" : "Create an account"}
          </button>
          <button className="auth-text-action muted" type="button" onClick={onBack}>
            Back to home
          </button>
        </div>
      </section>
    </main>
  );
}
