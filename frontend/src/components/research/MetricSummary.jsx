/** Render the three headline hybrid metrics without personalising them. */
export default function MetricSummary({ metrics }) {
  const hybrid = metrics.find((row) => row.model === "hybrid") || metrics[0];
  if (!hybrid) return null;
  const values = [
    {
      label: "Precision@5",
      value: Number(hybrid.precision_at_k).toFixed(4),
      note: "Relevant results among the top five",
    },
    {
      label: "Recall@5",
      value: Number(hybrid.recall_at_k).toFixed(4),
      note: "Relevant catalogue items recovered",
    },
    {
      label: "NDCG@5",
      value: Number(hybrid.ndcg_at_k).toFixed(4),
      note: "Ranking quality within the top five",
    },
  ];
  return (
    <div className="metric-summary" aria-label="Hybrid model evaluation metrics">
      {values.map((metric) => (
        <div key={metric.label}>
          <span>{metric.label}</span>
          <strong>{metric.value}</strong>
          <small>{metric.note}</small>
        </div>
      ))}
    </div>
  );
}
