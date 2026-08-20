/**
 * Manage authentication and the account-scoped session lifecycle.
 *
 * This hook owns auth API calls and session transitions. It must not generate
 * learning paths or mutate course progress.
 */
import { apiFetch } from "../lib/api";
import { emptySession, loadSession } from "../lib/session";

/**
 * Return authentication actions while preserving the app's existing states.
 */
export default function useAuthLifecycle({
  auth,
  setAuth,
  setError,
  setLastUpdate,
  setPath,
  setSession,
  setSkillCheckIds,
  setStep,
}) {
  function clearAuthentication(message = "") {
    setAuth({ authenticated: false, username: "" });
    setSession(emptySession);
    setPath(null);
    setLastUpdate(null);
    setSkillCheckIds([]);
    setError(message);
  }

  function handleExpiredSession() {
    clearAuthentication("Your session ended. Log in again to continue.");
    setStep("auth");
  }

  async function startLearning() {
    setError("");
    try {
      const response = await apiFetch("/api/auth/me");
      if (response.status === 401) {
        if (auth.authenticated) handleExpiredSession();
        else {
          clearAuthentication();
          setStep("auth");
        }
        return;
      }
      if (!response.ok) throw new Error("Could not verify your session.");
      const data = await response.json();
      const username = data.username || auth.username;
      const savedSession = loadSession(username);
      setAuth({ authenticated: true, username });
      setSession(savedSession);
      setPath(null);
      setLastUpdate(null);
      setSkillCheckIds([]);
      setStep(savedSession.selectedPathways.length > 0 ? "dashboard" : "pathways");
    } catch (requestError) {
      clearAuthentication(requestError.message || "Could not verify your session.");
      setStep("auth");
    }
  }

  async function submitAuth(mode, credentials) {
    setError("");
    const response = await apiFetch(`/api/auth/${mode}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(credentials),
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.detail || "Could not sign in.");
    const savedSession = loadSession(data.username);
    setAuth({ authenticated: true, username: data.username });
    setSession(savedSession);
    setPath(null);
    setLastUpdate(null);
    setSkillCheckIds([]);
    setStep(savedSession.selectedPathways.length > 0 ? "dashboard" : "pathways");
  }

  async function logout() {
    await apiFetch("/api/auth/logout", { method: "POST" }).catch(() => {});
    clearAuthentication();
    setStep("landing");
  }

  async function changePassword(payload) {
    setError("");
    const response = await apiFetch("/api/auth/change-password", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await response.json().catch(() => ({}));
    if (response.status === 401) {
      handleExpiredSession();
      throw new Error("Your session ended. Log in again to continue.");
    }
    if (!response.ok) throw new Error(data.detail || "Could not update the password.");
    setAuth({ authenticated: true, username: data.username || auth.username });
  }

  return {
    clearAuthentication,
    handleExpiredSession,
    publicActions: { changePassword, logout, startLearning, submitAuth },
  };
}
