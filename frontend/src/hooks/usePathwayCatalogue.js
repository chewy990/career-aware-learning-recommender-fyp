/**
 * Load pathway metadata used by selection and skill setup.
 *
 * This hook only loads catalogue metadata; it must not generate learner paths.
 */
import { useEffect } from "react";
import { apiFetch } from "../lib/api";

const STARTUP_ATTEMPTS = 30;
const RETRY_DELAY_MS = 3000;
const REQUEST_TIMEOUT_MS = 10000;

function wait(milliseconds, signal) {
  return new Promise((resolve) => {
    const timeout = window.setTimeout(resolve, milliseconds);
    signal.addEventListener(
      "abort",
      () => {
        window.clearTimeout(timeout);
        resolve();
      },
      { once: true },
    );
  });
}

async function fetchPathways(signal) {
  const requestController = new AbortController();
  const abortRequest = () => requestController.abort();
  const timeout = window.setTimeout(abortRequest, REQUEST_TIMEOUT_MS);
  signal.addEventListener("abort", abortRequest, { once: true });
  try {
    return await apiFetch("/api/pathways", {
      signal: requestController.signal,
    });
  } finally {
    window.clearTimeout(timeout);
    signal.removeEventListener("abort", abortRequest);
  }
}

/** Load pathway metadata once and initialise an empty pathway selection. */
export default function usePathwayCatalogue({
  setError,
  setLoading,
  setMeta,
  setSession,
  setStartupStatus,
}) {
  useEffect(() => {
    const controller = new AbortController();

    async function loadMeta() {
      setLoading(true);
      for (let attempt = 1; attempt <= STARTUP_ATTEMPTS; attempt += 1) {
        if (controller.signal.aborted) return;
        try {
          setStartupStatus(
            attempt === 1
              ? "Connecting to the recommendation service..."
              : "Preparing your learning experience. This can take up to one minute.",
          );
          const response = await fetchPathways(controller.signal);
          if (!response.ok) throw new Error("API did not respond cleanly.");
          const pathways = await response.json();
          setMeta(pathways);
          setSession((current) => ({
            ...current,
            selectedPathway:
              current.selectedPathway || pathways.pathways?.[0]?.id || "",
          }));
          setError("");
          setLoading(false);
          return;
        } catch (requestError) {
          if (controller.signal.aborted) return;
          if (attempt === STARTUP_ATTEMPTS) {
            setError(
              "The recommendation service did not start. Refresh to try again.",
            );
            setLoading(false);
            return;
          }
          await wait(RETRY_DELAY_MS, controller.signal);
        }
      }
    }
    loadMeta();
    return () => controller.abort();
  }, []);
}
