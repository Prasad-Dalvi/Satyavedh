import React from "react";
import "./SimilarityGauge.css";

/**
 * Renders a horizontal "distinct → duplicate" scale with a needle placed
 * by cosine similarity (0 to 1). Hash distance and verdict are printed
 * alongside like measurement readouts, rather than a generic score badge.
 */
export default function SimilarityGauge({ hashDistance, cosineSimilarity, verdict }) {
  const position = Math.min(Math.max(cosineSimilarity, 0), 1) * 100;

  return (
    <div className={`gauge gauge--${verdict}`}>
      <div className="gauge__scale">
        <div className="gauge__track" />
        <div className="gauge__needle" style={{ left: `${position}%` }} />
        <span className="gauge__label gauge__label--left mono">distinct</span>
        <span className="gauge__label gauge__label--right mono">duplicate</span>
      </div>
      <div className="gauge__readout mono">
        <span>hash Δ {hashDistance}</span>
        <span>cos {cosineSimilarity.toFixed(3)}</span>
        <span className="gauge__verdict">{verdict.replace("_", " ")}</span>
      </div>
    </div>
  );
}
