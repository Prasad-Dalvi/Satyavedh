import React, { useEffect, useState } from "react";
import { listImages, SERVER_ROOT } from "../services/api";
import "./Registry.css";

export default function Registry({ refreshKey }) {
  const [images, setImages] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    listImages()
      .then((data) => { if (!cancelled) setImages(data); })
      .catch(() => { if (!cancelled) setImages([]); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [refreshKey]);

  if (loading) return null;

  return (
    <section className="registry">
      <div className="registry__header">
        <span className="results__label mono">register</span>
        <h2>{images.length} image{images.length === 1 ? "" : "s"} on file</h2>
      </div>

      {images.length === 0 ? (
        <p className="registry__empty">Nothing logged yet — the first upload starts the register.</p>
      ) : (
        <ul className="registry__grid">
          {images.map((img) => (
            <li key={img._id} className="registry__cell">
              <img src={`${SERVER_ROOT}/uploads/${img.filename}`} alt={img.filename} />
              {img.aiLabel === "artificial" && (
                <span className="registry__tag mono" title="Flagged as possibly AI-generated">AI</span>
              )}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
