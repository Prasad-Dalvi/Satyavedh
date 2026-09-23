import React, { useState, useRef, useCallback } from "react";
import { uploadImage } from "../services/api";
import "./UploadPanel.css";

export default function UploadPanel({ onResult, onSubmittingChange }) {
  const [file, setFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [uploaderName, setUploaderName] = useState("");
  const [dragging, setDragging] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const inputRef = useRef(null);

  const setChosenFile = (f) => {
    if (!f) return;
    if (!f.type.startsWith("image/")) {
      setError("That file isn't an image.");
      return;
    }
    setError(null);
    setFile(f);
    setPreviewUrl(URL.createObjectURL(f));
  };

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setDragging(false);
    const f = e.dataTransfer.files?.[0];
    setChosenFile(f);
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) {
      setError("Place an image in the holder first.");
      return;
    }
    setLoading(true);
    onSubmittingChange?.(true);
    setError(null);
    try {
      const data = await uploadImage(file, uploaderName);
      onResult(data);
    } catch (err) {
      setError(err.response?.data?.error || "Comparison failed — is the server running?");
    } finally {
      setLoading(false);
      onSubmittingChange?.(false);
    }
  };

  return (
    <form className="upload" onSubmit={handleSubmit}>
      <div
        className={`upload__holder ${dragging ? "upload__holder--dragging" : ""} ${previewUrl ? "upload__holder--filled" : ""}`}
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") inputRef.current?.click(); }}
        aria-label="Choose an image to check"
      >
        <span className="upload__corner upload__corner--tl" />
        <span className="upload__corner upload__corner--tr" />
        <span className="upload__corner upload__corner--bl" />
        <span className="upload__corner upload__corner--br" />

        {previewUrl ? (
          <img src={previewUrl} alt="Selected preview" className="upload__preview" />
        ) : (
          <div className="upload__placeholder">
            <span className="upload__placeholder-icon">▭</span>
            <p>Drop an image here, or click to choose one</p>
          </div>
        )}
        <input
          ref={inputRef}
          type="file"
          accept="image/*"
          onChange={(e) => setChosenFile(e.target.files?.[0])}
          hidden
        />
      </div>

      <div className="upload__meta">
        <label className="upload__field">
          <span className="upload__field-label mono">submitted by</span>
          <input
            type="text"
            placeholder="optional"
            value={uploaderName}
            onChange={(e) => setUploaderName(e.target.value)}
          />
        </label>
        <button type="submit" className="upload__submit" disabled={loading}>
          {loading ? "Comparing…" : "Run comparison"}
        </button>
      </div>

      {error && <p className="upload__error mono">— {error}</p>}
    </form>
  );
}
