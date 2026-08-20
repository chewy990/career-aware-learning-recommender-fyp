/**
 * Compose the learner evidence and fixed-profile evaluation panels.
 *
 * Data loading and formatting live in focused research modules; this component
 * must not duplicate recommender calculations.
 */
import CurrentLearnerResearch from "./research/CurrentLearnerResearch";
import EvaluationDetails from "./research/EvaluationDetails";
import MetricSummary from "./research/MetricSummary";
import NdcgChart from "./research/NdcgChart";
import useResearchData from "./research/useResearchData";

export default function ResearchView({
  path,
  session,
  selectedPathway,
  coreSkillIds,
  onBack,
}) {
  const research = useResearchData();
  return (
    <div className="stack research-page">
      <div className="research-header">
        <div className="section-heading">
          <span>Research view</span>
          <h2>How your course was chosen</h2>
          <p>
            Inspect the learner inputs, resource-level evidence, and evaluation
            results behind the recommender.
          </p>
        </div>
        <button className="ghost inline-action" onClick={onBack}>
          Back to courses
        </button>
      </div>
      <CurrentLearnerResearch
        path={path}
        session={session}
        selectedPathway={selectedPathway}
        coreSkillIds={coreSkillIds}
      />

      <section className="model-performance">
        <div className="model-performance-header">
          <div>
            <span>Evaluation results</span>
            <h3>Model performance</h3>
            <p>
              Measured across fixed test profiles. These values evaluate the
              recommender, not your personal ability.
            </p>
          </div>
          <strong>Hybrid model</strong>
        </div>
        {research.metricsLoading ? (
          <div className="skeleton">Loading model metrics...</div>
        ) : (
          <>
            <MetricSummary metrics={research.metrics} />
            <NdcgChart metrics={research.metrics} />
          </>
        )}
        {research.error && <div className="error-banner">{research.error}</div>}
        <EvaluationDetails research={research} />
      </section>
      <button className="ghost" onClick={onBack}>Back to courses</button>
    </div>
  );
}
