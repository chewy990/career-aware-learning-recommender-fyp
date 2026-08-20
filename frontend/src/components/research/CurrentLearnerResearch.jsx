/**
 * Render evidence for the currently authenticated learner's course.
 *
 * This component preserves snapshot order and never displays raw model scores.
 */
import {
  compactList,
  DIFFICULTY_LABELS,
  formatDuration,
  normaliseSkillNames,
  readinessText,
  SKILL_LABELS,
} from "./formatters";

function EvidenceRow({ item, isNext = false }) {
  const skillLabels = item.skill_labels?.length
    ? item.skill_labels
    : (item.skills || []).map(
        (skill) => SKILL_LABELS[skill] || normaliseSkillNames(skill),
      );
  return (
    <article className={isNext ? "evidence-row next" : "evidence-row"}>
      <div className="evidence-resource">
        <span className="evidence-rank" aria-label={`Course position ${item.rank}`}>
          {String(item.rank).padStart(2, "0")}
        </span>
        <div>
          {isNext && <span className="evidence-kicker">Recommended next</span>}
          <strong>{item.title}</strong>
          <span>
            {item.provider || item.source} · {item.stage} ·{" "}
            {formatDuration(item.duration_hours)}
          </span>
        </div>
      </div>
      <dl className="evidence-facts">
        <div><dt>Targets</dt><dd>{skillLabels.join(", ") || "Pathway foundations"}</dd></div>
        <div>
          <dt>Level</dt>
          <dd>
            {item.difficulty_label ||
              DIFFICULTY_LABELS[item.difficulty_level] ||
              "Matched"}
          </dd>
        </div>
        <div>
          <dt>Prerequisites</dt>
          <dd className={item.ready ? "ready" : "locked"}>
            {readinessText(item)}
          </dd>
        </div>
      </dl>
    </article>
  );
}

export default function CurrentLearnerResearch({
  path,
  session,
  selectedPathway,
  coreSkillIds,
}) {
  const visibleItems = (path?.stages || [])
    .flatMap((stage) =>
      (stage.items || []).map((item) => ({ ...item, stage: stage.name })),
    )
    .map((item, index) => ({ ...item, rank: index + 1 }));
  const activeItems = visibleItems.filter((item) => !item.completed);
  const completedItems = visibleItems.filter((item) => item.completed);
  const coreIds = Array.from(coreSkillIds || []);
  const assessedSkills = coreIds.filter(
    (skillId) => Number(session?.skills?.[skillId] || 0) > 0,
  );
  const skillGaps = path?.skill_gaps || [];
  const highPriorityGaps = skillGaps.filter((gap) => gap.priority === "High");
  const priorityGaps = highPriorityGaps.length > 0 ? highPriorityGaps : skillGaps;
  const difficulty =
    DIFFICULTY_LABELS[
      path?.profile?.preferred_difficulty || session?.preferredDifficulty
    ] || "Beginner";
  const pathwayLabel =
    selectedPathway?.label ||
    path?.profile?.target_pathway_label ||
    "Not selected";

  if (!path) {
    return (
      <section className="current-research">
        <div className="research-note">
          Choose a pathway and generate a learning path first. This section will
          then show the relevant courses the system chose for you.
        </div>
      </section>
    );
  }
  const gapLabels = priorityGaps.map(
    (gap) => gap.label || SKILL_LABELS[gap.skill] || gap.skill,
  );
  return (
    <section className="current-research">
      <div className="research-inputs" aria-label="Recommendation inputs">
        <div><span>Pathway</span><strong>{pathwayLabel}</strong></div>
        <div><span>Preferred difficulty</span><strong>{difficulty}</strong></div>
        <div>
          <span>Assessed skills</span>
          <strong>
            {assessedSkills.length} of{" "}
            {coreIds.length || Object.keys(session?.skills || {}).length}
          </strong>
        </div>
        <div>
          <span>Course progress</span>
          <strong>{completedItems.length} of {visibleItems.length}</strong>
        </div>
      </div>
      <div className="research-priority-line">
        <span>Priority gaps</span>
        <strong>{gapLabels.length ? compactList(gapLabels) : "No remaining gaps"}</strong>
      </div>
      <div className="evidence-section-heading">
        <div>
          <h3>Recommendation evidence</h3>
          <p>
            Each resource is positioned by the skills it targets, its level,
            and whether its prerequisites are ready.
          </p>
        </div>
        <span>{activeItems.length} remaining</span>
      </div>
      <div className="evidence-list">
        {activeItems.length === 0 ? (
          <div className="research-note">
            All visible resources are completed. Switch pathways or review your
            completed history below.
          </div>
        ) : (
          activeItems.map((item, index) => (
            <EvidenceRow item={item} isNext={index === 0} key={item.item_id} />
          ))
        )}
      </div>
      {completedItems.length > 0 && (
        <details className="completed-research">
          <summary>Completed resources ({completedItems.length})</summary>
          <div className="completed-research-list">
            {completedItems.map((item) => (
              <div className="completed-evidence-row" key={item.item_id}>
                <strong>{item.title}</strong>
                <span>{item.provider || item.source} · {item.stage}</span>
              </div>
            ))}
          </div>
        </details>
      )}
    </section>
  );
}
