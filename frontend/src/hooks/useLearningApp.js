/**
 * Compose the learner workflow from focused hooks.
 *
 * This module owns top-level React state and the public controller contract. It
 * must not contain API request details or individual course/progress mutations.
 */
import { useEffect, useMemo, useState } from "react";
import {
  coreSkillsForPathway,
  isKnownSkill,
  loadAuth,
  loadSession,
  saveAuth,
  saveSession,
} from "../lib/session";
import useAuthLifecycle from "./useAuthLifecycle";
import useCourseActions from "./useCourseActions";
import useLearningPath from "./useLearningPath";
import usePathwayCatalogue from "./usePathwayCatalogue";
import useProgressActions from "./useProgressActions";

export default function useLearningApp() {
  const [meta, setMeta] = useState(null);
  const [auth, setAuth] = useState(loadAuth);
  const [session, setSession] = useState(() => loadSession(loadAuth().username));
  const [step, setStep] = useState("landing");
  const [path, setPath] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(null);
  const [skillCheckIds, setSkillCheckIds] = useState([]);
  const [loading, setLoading] = useState(true);
  const [startupStatus, setStartupStatus] = useState(
    "Connecting to the recommendation service...",
  );
  const [pathLoading, setPathLoading] = useState(false);
  const [error, setError] = useState("");
  const [confirmRequest, setConfirmRequest] = useState(null);

  // Persistence is account-scoped; never allow one user's learner state to
  // become the initial state for another authenticated account.
  useEffect(() => {
    saveSession(auth.username, session);
  }, [auth.username, session]);
  useEffect(() => {
    saveAuth(auth);
  }, [auth]);
  useEffect(() => {
    window.scrollTo({ top: 0, behavior: "auto" });
  }, [step]);
  usePathwayCatalogue({
    setError,
    setLoading,
    setMeta,
    setSession,
    setStartupStatus,
  });

  const authActions = useAuthLifecycle({
    auth,
    setAuth,
    setError,
    setLastUpdate,
    setPath,
    setSession,
    setSkillCheckIds,
    setStep,
  });

  const pathActions = useLearningPath({
    authActions,
    session,
    setError,
    setPath,
    setPathLoading,
    setSession,
    step,
  });

  const setupPathway = useMemo(
    () => meta?.pathways?.find((item) => item.id === session.selectedPathway),
    [meta, session.selectedPathway],
  );
  const activePathway = useMemo(
    () => meta?.pathways?.find((item) => item.id === session.activePathway),
    [meta, session.activePathway],
  );
  const coreSkills = useMemo(() => coreSkillsForPathway(setupPathway), [setupPathway]);
  const skillCheckIdSet = useMemo(() => new Set(skillCheckIds), [skillCheckIds]);
  const skillCheckSkills = useMemo(
    () => coreSkills.filter((skill) => skillCheckIdSet.has(skill.id)),
    [coreSkills, skillCheckIdSet],
  );
  const knownCoreSkills = useMemo(
    () =>
      coreSkills.filter(
        (skill) =>
          !skillCheckIdSet.has(skill.id) &&
          isKnownSkill(session.skills, skill.id),
      ),
    [coreSkills, session.skills, skillCheckIdSet],
  );
  const activeCoreSkillIds = useMemo(
    () => new Set(coreSkillsForPathway(activePathway).map((skill) => skill.id)),
    [activePathway],
  );

  const courseActions = useCourseActions({
    meta,
    session,
    setLastUpdate,
    setPath,
    setSession,
    setSkillCheckIds,
    setStep,
    requestConfirm: setConfirmRequest,
  });
  const progressActions = useProgressActions({
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
    requestConfirm: setConfirmRequest,
    loadLearningPath: pathActions.loadLearningPath,
  });

  return {
    activeCoreSkillIds,
    activePathway,
    auth,
    ...authActions.publicActions,
    confirmRequest,
    closeConfirm: () => setConfirmRequest(null),
    ...courseActions,
    coreSkills,
    error,
    knownCoreSkills,
    lastUpdate,
    loading,
    meta,
    path,
    pathLoading,
    ...progressActions,
    session,
    setSession,
    setSkillCheckIds,
    setStep,
    setupPathway,
    skillCheckSkills,
    step,
    startupStatus,
  };
}
