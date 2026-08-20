const STORAGE_KEY = "career-aware-recommender-session-v2";
const AUTH_STORAGE_KEY = "career-aware-recommender-auth-ui-v3";

export const SKILL_LEVELS = [
  { value: 0, label: "Not started" },
  { value: 1, label: "Basic" },
  { value: 2, label: "Working knowledge" },
  { value: 3, label: "Confident" },
];

const CORE_SKILL_IDS_BY_PATHWAY = {
  data_analyst: ["python", "sql", "statistics", "data_cleaning", "data_visualisation"],
  data_scientist: ["python", "statistics", "data_cleaning", "machine_learning", "model_evaluation"],
  data_engineer: ["python", "sql", "data_cleaning", "databases", "deployment"],
  ml_engineer: ["python", "machine_learning", "model_evaluation", "deployment", "programming"],
  software_developer: ["programming", "apis", "databases", "testing", "version_control"],
};

/** Return the learner-facing label for a numeric skill level. */
export function skillLevelLabel(level) {
  return SKILL_LEVELS.find((item) => item.value === Number(level))?.label || "Not started";
}

function knownSkillLevel(skills, skillId) {
  return Number(skills?.[skillId] || 0);
}

/** Return whether the learner has evidence above level zero for a skill. */
export function isKnownSkill(skills, skillId) {
  return knownSkillLevel(skills, skillId) > 0;
}

/** Return the stable five-skill core used by pathway setup and readiness. */
export function coreSkillsForPathway(pathway) {
  if (!pathway) return [];
  const coreIds = CORE_SKILL_IDS_BY_PATHWAY[pathway.id] || pathway.skills.slice(0, 5).map((skill) => skill.id);
  const pathwaySkills = new Map(pathway.skills.map((skill) => [skill.id, skill]));
  return coreIds.map((skillId) => pathwaySkills.get(skillId)).filter(Boolean);
}

function stageRequirement(stageName) {
  if (stageName.startsWith("3.")) return 2;
  if (stageName.startsWith("2.") || stageName.startsWith("Optional")) return 1;
  return 0;
}

function stageCourseType(stageName) {
  return stageName.startsWith("3.") ? "practice" : "foundation";
}

const SKILL_LABELS = {
  python: "Python",
  sql: "SQL",
  statistics: "Statistics",
  data_cleaning: "Data Cleaning",
  data_visualisation: "Data Visualisation",
  dashboarding: "Dashboarding",
  excel: "Excel",
  machine_learning: "Machine Learning",
  model_evaluation: "Model Evaluation",
  deployment: "Deployment",
  programming: "Programming",
  apis: "APIs",
  databases: "Databases",
  testing: "Testing",
  version_control: "Version Control",
};

function displaySkillLabel(skillId) {
  return SKILL_LABELS[skillId] || skillId.replace(/_/g, " ").replace(/\b\w/g, (char) => char.toUpperCase());
}

function formatChoiceList(items) {
  if (items.length === 0) return "a related skill";
  if (items.length === 1) return items[0];
  return `${items.slice(0, -1).join(", ")} or ${items.at(-1)}`;
}

/** Calculate display readiness without changing the scientific ranking order. */
export function itemReadiness(stageName, skills, itemSkills = []) {
  const requiredLevel = stageRequirement(stageName);
  if (requiredLevel === 0) return { ready: true, lockedReason: "" };
  if (itemSkills.some((skill) => Number(skills[skill] || 0) >= requiredLevel)) {
    return { ready: true, lockedReason: "" };
  }
  const needed = itemSkills.filter((skill) => Number(skills[skill] || 0) < requiredLevel);
  const labels = needed.slice(0, 2).map(displaySkillLabel);
  if (needed.length > 2) labels.push("a related skill");
  const skillText = formatChoiceList(labels);
  return {
    ready: false,
    lockedReason: `Unlock requirement: Complete a ${stageCourseType(stageName)} course in ${skillText} first.`,
  };
}

export const emptySession = {
  skills: {},
  completedTopics: [],
  completedItemIds: [],
  completedItems: [],
  pathSnapshots: {},
  selectedPathways: [],
  completedCourses: [],
  activePathway: "",
  selectedPathway: "",
  preferredDifficulty: 1,
  preferredFormat: "course",
};

/** Build the stable key that isolates cached paths by learner preferences. */
export function snapshotKeyFor(session, pathwayId) {
  return `${pathwayId}|${session.preferredDifficulty}|${session.preferredFormat}`;
}

function normaliseSession(savedSession) {
  const merged = { ...emptySession, ...(savedSession || {}) };
  return {
    ...merged,
    skills: merged.skills && typeof merged.skills === "object" ? merged.skills : {},
    completedTopics: Array.isArray(merged.completedTopics) ? merged.completedTopics : [],
    completedItemIds: Array.isArray(merged.completedItemIds) ? merged.completedItemIds : [],
    completedItems: Array.isArray(merged.completedItems) ? merged.completedItems : [],
    pathSnapshots: merged.pathSnapshots && typeof merged.pathSnapshots === "object"
      ? merged.pathSnapshots
      : {},
    selectedPathways: Array.isArray(merged.selectedPathways) ? merged.selectedPathways : [],
    completedCourses: Array.isArray(merged.completedCourses) ? merged.completedCourses : [],
  };
}

/** Copy a path while synchronising only its persisted completion flags. */
export function syncCompletedFlags(pathData, completedItemIds) {
  if (!pathData) return pathData;
  const completed = new Set(completedItemIds || []);
  return {
    ...pathData,
    stages: (pathData.stages || []).map((stage) => ({
      ...stage,
      items: (stage.items || []).map((item) => ({
        ...item,
        completed: completed.has(item.item_id),
      })),
    })),
  };
}

/** Refresh profile and readiness state while preserving item and stage order. */
export function refreshPathState(pathData, nextSession) {
  if (!pathData?.profile) return pathData;
  return {
    ...pathData,
    profile: {
      ...pathData.profile,
      current_skills: nextSession.skills,
      completed_topics: nextSession.completedTopics,
    },
    stages: (pathData.stages || []).map((stage) => ({
      ...stage,
      items: (stage.items || []).map((item) => {
        const completed = (nextSession.completedItemIds || []).includes(item.item_id);
        const readiness = itemReadiness(stage.name, nextSession.skills, item.skills);
        return {
          ...item,
          completed,
          ready: completed || readiness.ready,
          locked_reason: completed || readiness.ready ? "" : readiness.lockedReason,
        };
      }),
    })),
  };
}

/** Apply a completion transition to the displayed path without re-ranking it. */
export function markPathItemCompleted(pathData, itemId, nextSession) {
  return refreshPathState(syncCompletedFlags(pathData, nextSession.completedItemIds), nextSession);
}

function normaliseSessionOwner(username) {
  return (username || "").trim().toLowerCase();
}

function sessionKeyFor(username) {
  const owner = normaliseSessionOwner(username);
  return owner ? `${STORAGE_KEY}:${owner}` : "";
}

/** Load the account-scoped learner session, falling back safely on corrupt data. */
export function loadSession(username) {
  const key = sessionKeyFor(username);
  if (!key) return emptySession;
  try {
    const saved = window.localStorage.getItem(key);
    return saved ? normaliseSession(JSON.parse(saved)) : emptySession;
  } catch {
    return emptySession;
  }
}

/** Persist learner progress under the normalised account-scoped storage key. */
export function saveSession(username, session) {
  const key = sessionKeyFor(username);
  if (key) window.localStorage.setItem(key, JSON.stringify(session));
}

/** Load non-sensitive UI auth state; the server cookie remains authoritative. */
export function loadAuth() {
  try {
    const saved = window.sessionStorage.getItem(AUTH_STORAGE_KEY);
    if (!saved) return { authenticated: false, username: "" };
    const parsed = JSON.parse(saved);
    return {
      authenticated: Boolean(parsed?.authenticated),
      username: typeof parsed?.username === "string" ? parsed.username : "",
    };
  } catch {
    return { authenticated: false, username: "" };
  }
}

/** Persist only UI auth identity in session storage, never credentials or tokens. */
export function saveAuth(auth) {
  try {
    if (auth?.authenticated && auth?.username) {
      window.sessionStorage.setItem(
        AUTH_STORAGE_KEY,
        JSON.stringify({ authenticated: true, username: auth.username })
      );
    } else {
      window.sessionStorage.removeItem(AUTH_STORAGE_KEY);
    }
  } catch {
    // The server-side HttpOnly cookie remains the source of truth.
  }
}
