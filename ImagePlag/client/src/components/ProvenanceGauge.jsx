import React from "react";
import "./ProvenanceGauge.css";

/**
 * Shows how "synthetic-looking" the just-uploaded image reads across an
 * ensemble of detector models, plus the per-model breakdown -- deliberately
 * framed as an estimate, not a verdict. A single detector's blind spots are
 * common enough (no open-source model is a consistent winner across image
 * types) that showing agreement across models matters more than one score.
 */
export default function ProvenanceGauge({ label, confidence, agreement, models }) {
  const isArtificial = label === "artificial";
  const syntheticPosition = (isArtificial ? confidence : 1 - confidence) * 100;

  return (
    <section className="provenance">
      <div className="results__header">
        <span className="results__label mono">provenance estimate</span>
        <h2>{isArtificial ? "Reads as AI-generated" : "Reads as human-made"}</h2>
      </div>

      <div className="provenance__scale">
        <div className="provenance__track" />
        <div className="provenance__needle" style={{ left: `${syntheticPosition}%` }} />
        <span className="provenance__label provenance__label--left mono">human-made</span>
        <span className="provenance__label provenance__label--right mono">ai-generated</span>
      </div>
      <div className="provenance__readout mono">
        <span>confidence {(confidence * 100).toFixed(1)}%</span>
        {agreement && <span>· {agreement} models agree</span>}
      </div>

      {models && models.length > 0 && (
        <ul className="provenance__breakdown">
          {models.map((m) => (
            <li key={m.model} className="provenance__model-row">
              <span className="provenance__model-name mono">{m.model}</span>
              <span className={`provenance__model-verdict mono provenance__model-verdict--${m.label}`}>
                {m.label} · {(m.confidence * 100).toFixed(0)}%
              </span>
            </li>
          ))}
        </ul>
      )}

      <p className="provenance__disclaimer">
        This is an automated estimate from multiple pattern-based classifiers voting together,
        not a certified finding. It can be wrong, particularly on images from generators released
        after the detectors were trained — treat it as one signal, not a verdict.
      </p>
    </section>
  );
}
