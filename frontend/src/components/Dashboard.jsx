import useNextPathways from "../hooks/useNextPathways";
import PathStep from "./PathStep";

export default function Dashboard({ pathways, session, path, pathLoading, activeCoreSkillIds, onSwitchPathway, onDeletePathway, onComplete, lastUpdate, onStartPathway }) {
  const nextPathways = useNextPathways({ session, activePathway: session.activePathway });
  const selectedPathwaySet = new Set(session.selectedPathways);
  const selectedPathways = pathways.filter((pathway) => selectedPathwaySet.has(pathway.id));
  if (selectedPathways.length === 0) {
    return <div className="empty-state">No courses yet. Choose a pathway to generate your first course.</div>;
  }
  return (
    <div className="stack">
      <div className="dashboard-header">
        <div className="section-heading">
          <h2>My courses</h2>
        </div>
        <div className="course-switcher">
          <div className="course-switcher-heading">
            <strong>Select a pathway course</strong>
          </div>
          <div className="pathway-tabs" role="tablist" aria-label="Pathway courses">
            {selectedPathways.map((pathway) => {
              const isActive = session.activePathway === pathway.id;
              return (
                <button
                  className={isActive ? "pathway-tab active" : "pathway-tab"}
                  key={pathway.id}
                  role="tab"
                  aria-selected={isActive}
                  onClick={() => onSwitchPathway(pathway.id)}
                >
                  <span>{pathway.label}</span>
                  {isActive && <small>Viewing</small>}
                </button>
              );
            })}
          </div>
        </div>
      </div>
      <div className="course-slider" key={session.activePathway}>
        <PathStep
          path={path}
          pathLoading={pathLoading}
          coreSkillIds={activeCoreSkillIds}
          onComplete={onComplete}
          lastUpdate={lastUpdate}
          onStartPathway={onStartPathway}
          nextPathways={nextPathways}
        />
      </div>
      <details className="danger-zone">
        <summary>Manage pathways</summary>
        <div className="danger-zone-body">
          <p>Remove a course you no longer need. Shared skills and completed learning steps stay saved.</p>
          <div className="delete-pathway-list">
            {selectedPathways.map((pathway) => (
              <button className="danger-button" key={pathway.id} onClick={() => onDeletePathway(pathway.id)}>
                Remove {pathway.label}
              </button>
            ))}
          </div>
        </div>
      </details>
    </div>
  );
}
