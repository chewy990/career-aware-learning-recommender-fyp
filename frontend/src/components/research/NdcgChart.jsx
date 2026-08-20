/**
 * Draw the fixed-profile NDCG@5 comparison.
 *
 * Geometry is intentionally static so the graph remains reproducible.
 */
import { MODEL_LABELS } from "./formatters";

export default function NdcgChart({ metrics }) {
  const chartWidth = 640;
  const chartHeight = 260;
  const plotLeft = 58;
  const plotRight = 24;
  const plotTop = 30;
  const plotBottom = 212;
  const plotWidth = chartWidth - plotLeft - plotRight;
  const slotWidth = plotWidth / Math.max(metrics.length, 1);
  const barWidth = Math.min(94, slotWidth * 0.58);
  const ticks = [0, 0.25, 0.5, 0.75, 1];
  return (
    <div className="ndcg-card">
      <h3>NDCG@5 comparison</h3>
      <p>
        Higher values indicate that relevant resources appear closer to the top
        of the recommendation list.
      </p>
      <svg
        viewBox={`0 0 ${chartWidth} ${chartHeight}`}
        role="img"
        aria-label="NDCG at 5 comparison chart"
      >
        {ticks.map((tick) => {
          const y = plotBottom - tick * (plotBottom - plotTop);
          return (
            <g key={tick}>
              <line
                className="chart-grid-line"
                x1={plotLeft}
                y1={y}
                x2={chartWidth - plotRight}
                y2={y}
              />
              <text className="axis-label" x={plotLeft - 10} y={y + 4}>
                {tick.toFixed(2)}
              </text>
            </g>
          );
        })}
        {metrics.map((row, index) => {
          const value = Number(row.ndcg_at_k || 0);
          const x = plotLeft + index * slotWidth + (slotWidth - barWidth) / 2;
          const height = Math.max(2, value * (plotBottom - plotTop));
          const y = plotBottom - height;
          return (
            <g key={row.model}>
              <rect
                className={row.model === "hybrid" ? "model-bar primary" : "model-bar"}
                x={x}
                y={y}
                width={barWidth}
                height={height}
                rx="2"
              />
              <text className="bar-value" x={x + barWidth / 2} y={Math.max(18, y - 8)}>
                {value.toFixed(3)}
              </text>
              <text className="bar-label" x={x + barWidth / 2} y={plotBottom + 24}>
                {MODEL_LABELS[row.model] || row.model}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}
