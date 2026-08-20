/**
 * Render collapsible dataset, metric, and recommendation inspection controls.
 *
 * This panel exposes fixed-profile evidence and must not imply personal scores.
 */
import { MODEL_LABELS, normaliseExplanation } from "./formatters";

function MetricsTable({ metrics }) {
  return (
    <div className="metrics-table-wrap">
      <table className="metrics-table">
        <thead>
          <tr>
            <th>Model</th><th>K</th><th>Precision@K</th>
            <th>Recall@K</th><th>NDCG@K</th>
          </tr>
        </thead>
        <tbody>
          {metrics.map((row) => (
            <tr key={row.model}>
              <td>{MODEL_LABELS[row.model] || row.model}</td>
              <td>{row.k}</td>
              <td>{Number(row.precision_at_k).toFixed(4)}</td>
              <td>{Number(row.recall_at_k).toFixed(4)}</td>
              <td>{Number(row.ndcg_at_k).toFixed(4)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function DatasetSummary({ summary }) {
  const rows = [
    ["Learning resources", summary.learning_resources],
    ["Verified modules", summary.verified_modules],
    ["Learner profiles", summary.learner_profiles],
    ["Relevance profiles", summary.relevance_profiles],
    ["Pathways", summary.pathways],
    ["Skills", summary.skills],
    ["Output folder", summary.output_folder],
  ];
  return (
    <details className="dataset-summary">
      <summary>Dataset summary</summary>
      <div className="dataset-grid">
        {rows.map(([label, value]) => (
          <div key={label}><span>{label}</span><strong>{value}</strong></div>
        ))}
      </div>
    </details>
  );
}

export default function EvaluationDetails({ research }) {
  return (
    <details className="advanced-research">
      <summary>Detailed evaluation data</summary>
      <div className="advanced-research-content">
        <p>
          The full metric table, dataset summary, and fixed-profile examples are
          provided for closer model inspection.
        </p>
        <MetricsTable metrics={research.metrics} />
        {research.datasetSummary && <DatasetSummary summary={research.datasetSummary} />}
        <details className="evaluation-examples">
          <summary>Model example recommendations</summary>
          <p>
            These use fixed sample profiles from the evaluation dataset. They
            are for model inspection, not your personal learner state.
          </p>
          <div className="research-controls">
            <label className="field">
              <span>Evaluation profile</span>
              <select
                value={research.profileId}
                onChange={(event) => research.setProfileId(event.target.value)}
              >
                {research.profiles.map((profile) => (
                  <option key={profile.profile_id} value={profile.profile_id}>
                    {profile.name} - {profile.target_pathway_label}
                  </option>
                ))}
              </select>
            </label>
            <label className="field">
              <span>Model</span>
              <select
                value={research.model}
                onChange={(event) => research.setModel(event.target.value)}
              >
                <option value="hybrid">Hybrid</option>
                <option value="content_based">Content based</option>
                <option value="popularity">Popularity</option>
              </select>
            </label>
            <label className="field">
              <span>Top K</span>
              <select
                value={research.topK}
                onChange={(event) => research.setTopK(Number(event.target.value))}
              >
                {[3, 5, 10].map((value) => (
                  <option key={value} value={value}>{value}</option>
                ))}
              </select>
            </label>
          </div>
          {research.loading ? (
            <div className="skeleton">Loading research results...</div>
          ) : (
            <div className="research-list">
              {research.recommendations.map((item) => (
                <article
                  className="research-row"
                  key={`${item.rank}-${item.resource_id}`}
                >
                  <strong>#{item.rank} {item.title}</strong>
                  <span>{item.provider} | Score {Number(item.score).toFixed(3)}</span>
                  <p>{normaliseExplanation(item.explanation)}</p>
                </article>
              ))}
            </div>
          )}
        </details>
      </div>
    </details>
  );
}
