import { ArrowRight, LockKeyhole } from "lucide-react";
import { skillLevelLabel } from "../lib/session";

function formatDuration(hours) {
  const value = Number(hours);
  const amount = value.toLocaleString(undefined, { maximumFractionDigits: 2 });
  return `${amount} ${value === 1 ? "hour" : "hours"}`;
}

function Stage({ stage, onComplete, defaultOpen }) {
  return (
    <details className="stage" open={defaultOpen}>
      <summary>{stage.name}</summary>
      {stage.items.length === 0 ? (
        <div className="empty-stage">Completed items remain visible. No new useful next steps for this stage right now.</div>
      ) : stage.items.map((item) => (
        <article className={item.completed ? "resource completed" : "resource"} key={item.item_id}>
          <label className="complete-line">
            <input type="checkbox" checked={item.completed} disabled={item.completed || !item.ready} onChange={() => onComplete(stage.name, item)} />
            <span>{item.completed ? "Completed" : item.ready ? "Mark complete" : "Locked"}</span>
          </label>
          {!item.ready && (
            <div className="lock-note" role="note">
              <LockKeyhole aria-hidden="true" />
              <span>
                <strong>Unlock requirement</strong>
                {item.locked_reason.replace(/^Unlock requirement:\s*/i, "")}
              </span>
            </div>
          )}
          <h3>{item.title}</h3>
          {item.source_url ? <a href={item.source_url} target="_blank" rel="noreferrer">{item.source}</a> : <p>{item.source}</p>}
          <div className="meta-line">{item.difficulty_label} | {formatDuration(item.duration_hours)}</div>
          <p>{item.reason}</p>
        </article>
      ))}
    </details>
  );
}

const TOP_SKILLS = 3;

export default function PathStep({ path, pathLoading, coreSkillIds, onComplete, lastUpdate, onStartPathway, nextPathways = [] }) {
  if (pathLoading && !path) return <div className="skeleton">Generating staged path...</div>;
  if (!path) return <div className="empty-state">Choose a pathway to generate your learning path.</div>;
  const visibleSkillGaps = (path.skill_gaps || []).filter((gap) => coreSkillIds.has(gap.skill));
  const visibleItems = (path.stages || []).flatMap((stage) =>
    (stage.items || []).map((item) => ({ ...item, stageName: stage.name }))
  );
  const completedCount = visibleItems.filter((item) => item.completed).length;
  const totalCount = visibleItems.length;
  const progressPercent = totalCount > 0 ? Math.round((completedCount / totalCount) * 100) : 0;
  const nextItem = visibleItems.find((item) => item.ready && !item.completed);
  const nextStageName = nextItem?.stageName || (path.stages || []).find((stage) =>
    (stage.items || []).some((item) => !item.completed)
  )?.name;
  const courseComplete = visibleItems.length > 0 && visibleItems.every((item) => item.completed);
  return (
    <div className="stack">
      <div className="path-header">
        <h2>
          <span>{path.profile.target_pathway_label}</span>
          <small>{completedCount} of {totalCount} steps</small>
        </h2>
      </div>
      <div
        className="course-progress"
        role="progressbar"
        aria-label={`${path.profile.target_pathway_label} course progress`}
        aria-valuemin="0"
        aria-valuemax={totalCount}
        aria-valuenow={completedCount}
      >
        <span style={{ transform: `scaleX(${progressPercent / 100})` }} />
      </div>

      {nextItem && (
        <section className="continue-panel">
          <div>
            <span className="continue-eyebrow">Continue learning</span>
            <h3>{nextItem.title}</h3>
            <p>{nextItem.stageName} | {nextItem.difficulty_label} | {formatDuration(nextItem.duration_hours)}</p>
          </div>
          {nextItem.source_url && (
            <a className="primary continue-link" href={nextItem.source_url} target="_blank" rel="noreferrer">
              Open resource
            </a>
          )}
        </section>
      )}

      {lastUpdate && (
        <div className="progress-note">
          <strong>Completed {lastUpdate.title}</strong>
          {lastUpdate.skillChanges.length > 0 ? (
            <div className="skill-change-list">
              {lastUpdate.skillChanges.map((change) => (
                <div className="skill-change" key={change.skill}>
                  <span>{change.label}</span>
                  <div className="skill-change-levels">
                    <b>{change.before_label || skillLevelLabel(change.before)}</b>
                    <i aria-hidden="true">&gt;</i>
                    <b>{change.after_label || skillLevelLabel(change.after)}</b>
                  </div>
                </div>
              ))}
            </div>
          ) : <p>Skills reinforced.</p>}
        </div>
      )}

      {(path.course_complete || path.mastery || courseComplete) && (
        <div className="course-complete-note">
          <strong>Congratulations, you completed this course!</strong>
          <p>You finished every step in it. The course targets the highest-priority gaps for this pathway rather than every skill the role asks for, so there is more you can deepen later.</p>

          {nextPathways.length > 0 && (
            <div className="next-pathways">
              <span className="next-pathways-title">Where this can take you next</span>
              <p className="next-pathways-lede">
                Share of each pathway's requirement you already meet.
              </p>
              {nextPathways.map((option) => {
                const percent = Math.round(option.coverage * 100);
                const shown = option.remaining.slice(0, TOP_SKILLS);
                const more = option.remaining.length - shown.length;
                return (
                  <div className="next-pathway" key={option.pathway}>
                    <div className="next-pathway-head">
                      <b>{option.label}</b>
                      <span className="next-pathway-coverage">{percent}%</span>
                    </div>
                    <div
                      className="next-pathway-bar"
                      role="progressbar"
                      aria-label={`${option.label} requirement already met`}
                      aria-valuemin="0"
                      aria-valuemax="100"
                      aria-valuenow={percent}
                    >
                      <span style={{ transform: `scaleX(${option.coverage})` }} />
                    </div>
                    <div className="next-pathway-foot">
                      {shown.length > 0 && (
                        <p className="next-pathway-skills">
                          {shown.map((item) => item.label).join(' · ')}
                          {more > 0 && ` · and ${more} more`}
                        </p>
                      )}
                      {onStartPathway && (
                        <button
                          type="button"
                          className="next-pathway-action"
                          onClick={() => onStartPathway(option.pathway)}
                        >
                          Start {option.label}
                          <ArrowRight aria-hidden="true" />
                        </button>
                      )}
                    </div>
                  </div>
                );
              })}
              <p className="next-pathways-note">
                Based on skills these pathways share, not on career outcomes.
              </p>
            </div>
          )}
        </div>
      )}

      <div className="stage-list">
        {path.stages.map((stage) => (
          <Stage
            key={stage.name}
            stage={stage}
            onComplete={onComplete}
            defaultOpen={stage.name === nextStageName}
          />
        ))}
      </div>

      <details className="skill-gap-panel">
        <summary>Remaining skill gaps ({visibleSkillGaps.length})</summary>
        {visibleSkillGaps.length === 0 ? <p>No actionable core gaps right now.</p> : visibleSkillGaps.map((gap) => (
          <div className="gap-row" key={gap.skill}>
            <span>{gap.label}</span>
            <small>{gap.priority}</small>
            <b>
              <span>{gap.current_label || skillLevelLabel(gap.current)}</span>
              <i aria-hidden="true">&gt;</i>
              <span>{gap.target_label || skillLevelLabel(gap.target)}</span>
            </b>
          </div>
        ))}
      </details>
    </div>
  );
}
