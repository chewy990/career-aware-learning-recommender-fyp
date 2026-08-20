/**
 * Apply completion and reset transitions to learner progress.
 *
 * Completed items remain in their original snapshot order. This hook must not
 * regenerate ranking logic or own pathway membership.
 */
import { apiFetch } from "../lib/api";
import {
  markPathItemCompleted,
  snapshotKeyFor,
} from "../lib/session";

/** Return completion and reset actions for the active learner session. */
export default function useProgressActions({
  authActions,
  path,
  session,
  setError,
  setLastUpdate,
  setPath,
  setSession,
  setSkillCheckIds,
  setStep,
  step,
  requestConfirm,
  loadLearningPath,
}) {
  async function completeItem(stageName, item) {
    if (session.completedItemIds.includes(item.item_id)) return;
    const response = await apiFetch("/api/complete-item", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        target_pathway: session.activePathway,
        stage: stageName,
        current_skills: session.skills,
        completed_topics: session.completedTopics,
        topic: item.topic,
        skills: item.skills,
      }),
    });
    if (response.status === 401) {
      authActions.handleExpiredSession();
      return;
    }
    if (!response.ok) {
      setError("Could not save this completed step.");
      return;
    }

    const result = await response.json();
    const completedRecord = {
      item_id: item.item_id,
      resource_id: item.resource_id,
      title: item.title,
      stage: stageName,
      source: item.source,
      source_url: item.source_url,
      reason: item.reason,
      skill_changes: result.skill_changes || [],
    };
    const completedItemIds = [...session.completedItemIds, item.item_id];
    const snapshotKey = snapshotKeyFor(session, session.activePathway);
    // A finished course is recorded permanently, so removing it later never
    // makes the pathway eligible to be recommended again.
    const done = new Set(completedItemIds);
    const stillOpen = (path?.stages || []).some((stage) =>
      (stage.items || []).some((entry) => !done.has(entry.item_id)),
    );
    const completedCourses =
      !stillOpen && session.activePathway &&
      !session.completedCourses.includes(session.activePathway)
        ? [...session.completedCourses, session.activePathway]
        : session.completedCourses;
    const next = {
      ...session,
      completedCourses,
      skills: result.current_skills || session.skills,
      completedTopics: result.completed_topics || session.completedTopics,
      completedItemIds,
      completedItems: [...session.completedItems, completedRecord],
      pathSnapshots: {
        ...(session.pathSnapshots || {}),
        [snapshotKey]: path || session.pathSnapshots?.[snapshotKey],
      },
    };
    setLastUpdate({ title: item.title, skillChanges: result.skill_changes || [] });
    setSession(next);
    setPath(markPathItemCompleted(path, item.item_id, next));
  }

  function resetProgress() {
    requestConfirm({
      title: "Reset all completed learning steps?",
      message:
        "Your saved skill levels and generated courses stay available. Only completed steps are cleared.",
      confirmLabel: "Reset progress",
      onConfirm: applyResetProgress,
    });
  }

  function applyResetProgress() {
    const next = {
      ...session,
      completedItemIds: [],
      completedItems: [],
      completedTopics: [],
      completedCourses: [],
      pathSnapshots: {},
    };
    setSession(next);
    setLastUpdate(null);
    if (step === "dashboard" || step === "research") {
      loadLearningPath(next, next.activePathway);
    }
  }

  function resetSkills() {
    requestConfirm({
      title: "Reset all saved skill levels?",
      message:
        "Completed learning steps stay saved, but you will assess your skills again before generating a course.",
      confirmLabel: "Reset skills",
      onConfirm: applyResetSkills,
    });
  }

  function applyResetSkills() {
    setSession({ ...session, skills: {}, pathSnapshots: {} });
    setPath(null);
    setLastUpdate(null);
    setSkillCheckIds([]);
    setStep("pathways");
  }

  return { completeItem, resetProgress, resetSkills };
}
