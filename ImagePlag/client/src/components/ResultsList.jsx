import React from "react";
import SimilarityGauge from "./SimilarityGauge";
import { SERVER_ROOT } from "../services/api";
import "./ResultsList.css";

export default function ResultsList({ result }) {
  if (!result) return null;

  const { matches, matchCount } = result;

  return (
    <section className="results">
      <div className="results__header">
        <span className="results__label mono">finding</span>
        <h2>
          {matchCount === 0
            ? "No prior record found"
            : `${matchCount} prior record${matchCount > 1 ? "s" : ""} match`}
        </h2>
      </div>

      {matchCount === 0 && (
        <p className="results__empty">
          This image doesn't resemble anything already in the register. It's been logged as a new original.
        </p>
      )}

      <ul className="results__list">
        {matches.map((m) => (
          <li key={m.imageId} className="results__item">
            <img
              className="results__thumb"
              src={`${SERVER_ROOT}/uploads/${m.filename}`}
              alt={m.filename}
            />
            <div className="results__body">
              <div className="results__title">
                <span>{m.filename}</span>
                <span className="results__uploader mono">— submitted by {m.uploaderName}</span>
              </div>
              <SimilarityGauge
                hashDistance={m.hash_distance}
                cosineSimilarity={m.cosine_similarity}
                verdict={m.verdict}
              />
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
}
