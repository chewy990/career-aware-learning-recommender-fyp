/**
 * Load, cache, and refresh learning-path snapshots.
 *
 * Snapshot identity and recommendation order are compatibility contracts. This
 * hook must not alter ranking, completion logic, or pathway selection.
 */
import { useEffect, useRef } from "react";
import { apiFetch } from "../lib/api";
import {
  refreshPathState,
  snapshotKeyFor,
  syncCompletedFlags,
} from "../lib/session";

/**
 * Provide the single path-loading operation used by all learner flows.
 */
export default function useLearningPath({
  authActions,
  session,
  setError,
  setPath,
  setPathLoading,
  setSession,
  step,
}) {
  const requestSequence = useRef(0);

  async function loadLearningPath(
    nextSession = session,
    pathwayId = nextSession.activePathway || nextSession.selectedPathway,
  ) {
    const requestId = requestSequence.current + 1;
    requestSequence.current = requestId;
    if (!pathwayId) {
      setPathLoading(false);
      return null;
    }

    const key = snapshotKeyFor(nextSession, pathwayId);
    const savedSnapshot = nextSession.pathSnapshots?.[key];
    if (savedSnapshot && nextSession.completedItemIds.length > 0) {
      const refreshedPath = refreshPathState(
        syncCompletedFlags(savedSnapshot, nextSession.completedItemIds),
        nextSession,
      );
      if (requestId === requestSequence.current) {
        setPath(refreshedPath);
        setPathLoading(false);
      }
      return refreshedPath;
    }
    if (savedSnapshot) {
      const pathWithFlags = syncCompletedFlags(
        savedSnapshot,
        nextSession.completedItemIds,
      );
      if (requestId === requestSequence.current) {
        setPath(pathWithFlags);
        setPathLoading(false);
      }
      return savedSnapshot;
    }

    setPathLoading(true);
    setError("");
    try {
      const response = await apiFetch("/api/learning-path", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          target_pathway: pathwayId,
          current_skills: nextSession.skills,
          completed_topics: nextSession.completedTopics,
          completed_item_ids: nextSession.completedItemIds,
          preferred_difficulty: nextSession.preferredDifficulty,
          preferred_format: nextSession.preferredFormat,
          profile_id: "react_custom",
          name: "Custom learner",
        }),
      });
      if (response.status === 401) {
        authActions.handleExpiredSession();
        throw new Error("Your session ended. Log in again to continue.");
      }
      if (!response.ok) throw new Error("Could not generate the learning path.");
      const generatedPath = await response.json();
      if (requestId !== requestSequence.current) return null;
      const pathWithFlags = syncCompletedFlags(
        generatedPath,
        nextSession.completedItemIds,
      );
      setPath(pathWithFlags);
      // Preserve an existing snapshot: it fixes the displayed ordering while
      // completion flags are refreshed independently.
      setSession((current) => {
        if (current.pathSnapshots?.[key]) return current;
        return {
          ...current,
          pathSnapshots: { ...(current.pathSnapshots || {}), [key]: pathWithFlags },
        };
      });
      return pathWithFlags;
    } catch (requestError) {
      if (requestId === requestSequence.current) {
        setError(requestError.message || "Could not generate the learning path.");
      }
      return null;
    } finally {
      if (requestId === requestSequence.current) setPathLoading(false);
    }
  }

  useEffect(() => {
    const needsPath =
      (step === "dashboard" || step === "research") && session.activePathway;
    if (needsPath) loadLearningPath(session, session.activePathway);
  }, [
    session.activePathway,
    session.preferredDifficulty,
    session.preferredFormat,
    step,
  ]);

  return { loadLearningPath };
}
