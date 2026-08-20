/**
 * Format research evidence for learner-facing display.
 *
 * These helpers only transform labels and prose; they must not alter scores.
 */
export const SKILL_LABELS = {
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

export const DIFFICULTY_LABELS = {
  1: "Beginner",
  2: "Intermediate",
  3: "Advanced",
};

export const MODEL_LABELS = {
  popularity: "Popularity",
  content_based: "Content based",
  hybrid: "Hybrid",
};

export function normaliseSkillNames(value) {
  return Object.entries(SKILL_LABELS).reduce((text, [skillId, label]) => {
    const skillPattern = skillId.replace(/_/g, "[_ ]");
    return text.replace(new RegExp(`\\b${skillPattern}\\b`, "gi"), label);
  }, value);
}

export function normaliseExplanation(explanation) {
  if (!explanation) {
    return "This resource matches your current pathway and progression needs.";
  }
  let text = normaliseSkillNames(explanation)
    .replace(/^Recommended because\s+/i, "")
    .replace(/\bthe learner's current level\b/gi, "your current level")
    .replace(
      /\bthe learner appears to meet the prerequisites\b/gi,
      "you appear to meet the prerequisites",
    )
    .replace(/\.$/, "");
  if (/^This resource\b/i.test(text)) return `${text}.`;
  if (/^Practise\s+/i.test(text)) {
    return `This resource gives you practical work with ${text.replace(/^Practise\s+/i, "")}.`;
  }
  if (/^Deepen\s+/i.test(text)) {
    return `This resource was chosen to deepen your knowledge of ${text.replace(/^Deepen\s+/i, "")}.`;
  }
  if (/^Optional reinforcement for\s+/i.test(text)) {
    return `This optional resource reinforces ${text.replace(/^Optional reinforcement for\s+/i, "")}.`;
  }
  if (/^Targets\s+/i.test(text)) text = `it targets ${text.replace(/^Targets\s+/i, "")}`;
  return `This resource was chosen because ${text}.`;
}

export function formatDuration(hours) {
  const value = Number(hours || 0);
  if (!value) return "Self-paced";
  return `${value} ${value === 1 ? "hour" : "hours"}`;
}

export function compactList(items, limit = 3) {
  if (items.length <= limit) return items.join(", ");
  return `${items.slice(0, limit).join(", ")} +${items.length - limit} more`;
}

export function readinessText(item) {
  if (item.ready) return "Ready";
  return (item.locked_reason || "Complete an earlier foundation resource first.")
    .replace(/^Unlock requirement:\s*/i, "");
}
