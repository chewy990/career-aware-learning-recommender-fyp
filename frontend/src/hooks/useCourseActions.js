/**
 * Manage pathway selection and generated-course membership.
 *
 * This hook must not own authentication or completion mutations.
 */
import {
  coreSkillsForPathway,
  isKnownSkill,
} from "../lib/session";

/** Return pathway and course actions backed by the shared learner session. */
export default function useCourseActions({
  meta,
  session,
  setLastUpdate,
  setPath,
  setSession,
  setSkillCheckIds,
  setStep,
  requestConfirm,
}) {
  function updateSkill(skillId, value) {
    setSession((current) => ({
      ...current,
      skills: { ...current.skills, [skillId]: Number(value) },
    }));
  }

  function choosePathway(pathwayId) {
    const nextPathway = meta?.pathways?.find((item) => item.id === pathwayId);
    const nextSkillCheckIds = coreSkillsForPathway(nextPathway)
      .filter((skill) => !isKnownSkill(session.skills, skill.id))
      .map((skill) => skill.id);
    setSession({ ...session, selectedPathway: pathwayId });
    setPath(null);
    setLastUpdate(null);
    setSkillCheckIds(nextSkillCheckIds);
    setStep("skills");
  }

  function generateCourse() {
    if (!session.selectedPathway) return;
    const selectedPathways = session.selectedPathways.includes(
      session.selectedPathway,
    )
      ? session.selectedPathways
      : [...session.selectedPathways, session.selectedPathway];
    const next = {
      ...session,
      selectedPathways,
      activePathway: session.selectedPathway,
    };
    setSession(next);
    setLastUpdate(null);
    setStep("dashboard");
  }

  function switchActivePathway(pathwayId) {
    const next = {
      ...session,
      activePathway: pathwayId,
      selectedPathway: pathwayId,
    };
    setSession(next);
    setLastUpdate(null);
  }

  function deletePathway(pathwayId) {
    const pathwayLabel =
      meta?.pathways?.find((item) => item.id === pathwayId)?.label ||
      "this pathway";
    requestConfirm({
      title: `Remove ${pathwayLabel}?`,
      message:
        "This course is removed from My courses. Your saved skills and completed learning steps stay saved.",
      confirmLabel: "Remove course",
      onConfirm: () => removePathway(pathwayId),
    });
  }

  function removePathway(pathwayId) {
    const selectedPathways = session.selectedPathways.filter(
      (item) => item !== pathwayId,
    );
    const activePathwayId =
      session.activePathway === pathwayId
        ? selectedPathways[0] || ""
        : session.activePathway;
    const pathSnapshots = Object.fromEntries(
      Object.entries(session.pathSnapshots || {}).filter(
        ([key]) => !key.startsWith(`${pathwayId}|`),
      ),
    );
    const next = {
      ...session,
      selectedPathways,
      activePathway: activePathwayId,
      selectedPathway: activePathwayId || session.selectedPathway,
      pathSnapshots,
    };
    setSession(next);
    setLastUpdate(null);
    if (!activePathwayId) {
      setPath(null);
      setStep("pathways");
    }
  }

  return {
    choosePathway,
    deletePathway,
    generateCourse,
    switchActivePathway,
    updateSkill,
  };
}
