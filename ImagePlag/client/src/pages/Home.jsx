import React, { useEffect, useRef, useState } from "react";
import * as THREE from "three";
import { listImages, uploadImage, SERVER_ROOT } from "../services/api";
import "./Home.css";

export default function Home() {
  const [result, setResult] = useState(null);
  const [registry, setRegistry] = useState([]);
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState("");
  const [uploaderName, setUploaderName] = useState("");
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const inputRef = useRef(null);
  const canvasRef = useRef(null);

  useEffect(() => {
    const container = canvasRef.current;
    if (!container) return undefined;

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 1000);
    camera.position.z = 34;
    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(window.innerWidth, window.innerHeight);
    container.appendChild(renderer.domElement);

    const shell = new THREE.Mesh(
      new THREE.IcosahedronGeometry(10, 2),
      new THREE.MeshBasicMaterial({ color: 0x22d3ee, wireframe: true, transparent: true, opacity: 0.14 }),
    );
    const core = new THREE.Mesh(
      new THREE.OctahedronGeometry(5.5, 1),
      new THREE.MeshBasicMaterial({ color: 0x818cf8, wireframe: true, transparent: true, opacity: 0.16 }),
    );
    const ring = new THREE.Mesh(
      new THREE.TorusGeometry(13, 0.12, 12, 96),
      new THREE.MeshBasicMaterial({ color: 0x22d3ee, wireframe: true, transparent: true, opacity: 0.22 }),
    );
    ring.rotation.x = Math.PI / 3;
    ring.position.set(-9, 5, -8);
    scene.add(shell, core, ring);

    const particleCount = 240;
    const positions = new Float32Array(particleCount * 3);
    for (let index = 0; index < positions.length; index += 3) {
      positions[index] = (Math.random() - 0.5) * 90;
      positions[index + 1] = (Math.random() - 0.5) * 65;
      positions[index + 2] = (Math.random() - 0.5) * 45;
    }
    const particleGeometry = new THREE.BufferGeometry();
    particleGeometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
    const particles = new THREE.Points(
      particleGeometry,
      new THREE.PointsMaterial({ color: 0x38bdf8, size: 0.22, transparent: true, opacity: 0.45 }),
    );
    scene.add(particles);

    let targetX = 0;
    let targetY = 0;
    let currentX = 0;
    let currentY = 0;
    const onPointerMove = (event) => {
      targetX = (event.clientX - window.innerWidth / 2) * 0.0008;
      targetY = (event.clientY - window.innerHeight / 2) * 0.0008;
    };
    const onResize = () => {
      camera.aspect = window.innerWidth / window.innerHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(window.innerWidth, window.innerHeight);
    };
    window.addEventListener("pointermove", onPointerMove);
    window.addEventListener("resize", onResize);
    let animationFrame;
    const animate = () => {
      animationFrame = requestAnimationFrame(animate);
      shell.rotation.x += 0.0015;
      shell.rotation.y += 0.0025;
      core.rotation.x -= 0.002;
      core.rotation.y -= 0.003;
      ring.rotation.z += 0.0025;
      particles.rotation.y += 0.00035;
      currentX += (targetX - currentX) * 0.04;
      currentY += (targetY - currentY) * 0.04;
      scene.rotation.y = currentX;
      scene.rotation.x = currentY;
      renderer.render(scene, camera);
    };
    animate();

    return () => {
      cancelAnimationFrame(animationFrame);
      window.removeEventListener("pointermove", onPointerMove);
      window.removeEventListener("resize", onResize);
      shell.geometry.dispose();
      shell.material.dispose();
      core.geometry.dispose();
      core.material.dispose();
      ring.geometry.dispose();
      ring.material.dispose();
      particleGeometry.dispose();
      particles.material.dispose();
      renderer.dispose();
      renderer.domElement.remove();
    };
  }, []);

  const refreshRegistry = () => listImages().then(setRegistry).catch(() => {});

  useEffect(() => {
    refreshRegistry();
  }, []);

  const chooseFile = (selected) => {
    if (!selected) return;
    if (!selected.type.startsWith("image/")) {
      setError("Please choose a valid image file.");
      return;
    }
    setError("");
    setFile(selected);
    setPreview(URL.createObjectURL(selected));
  };

  const submit = async (event) => {
    event.preventDefault();
    if (!file) {
      setError("Choose an image before starting the scan.");
      return;
    }
    setLoading(true);
    setError("");
    setResult(null);
    setStatus("Uploading image...\nRunning perceptual and AI analysis...");
    try {
      const data = await uploadImage(file, uploaderName);
      setResult(data);
      setStatus(`Scan complete.\n${data.matchCount || 0} possible duplicate matches found.`);
      refreshRegistry();
    } catch (err) {
      setError(err.response?.data?.error || "Analysis failed. Is the ImagePlag server running?");
      setStatus("");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="satyavedh">
      <div ref={canvasRef} className="canvas3d" aria-hidden="true" />
      <div className="ambient ambient-cyan" aria-hidden="true" />
      <div className="ambient ambient-indigo" aria-hidden="true" />
      <header className="topbar">
        <div className="brand"><span className="brand-mark">◈</span><span>Satyavedh</span><small>IMAGE FORENSICS</small></div>
        <div className="system-status"><span className="status-dot" /> IMAGE ANALYZER ONLINE</div>
      </header>

      <section className="hero">
        <span className="eyebrow">AI SYNTHETIC MEDIA VERIFICATION ENGINE</span>
        <h1>Image originality,<br /><em>made visible.</em></h1>
        <p>Upload an image to check its AI provenance and compare it against every image already registered.</p>
      </section>

      <section className="scan-card">
        <div className="scan-header"><span>01 / SUBMIT EVIDENCE</span><span className="mono">HASH + EMBEDDING + AI</span></div>
        <form onSubmit={submit}>
          <div
            className={`dropzone ${preview ? "has-preview" : ""}`}
            onClick={() => inputRef.current?.click()}
            onDragOver={(event) => event.preventDefault()}
            onDrop={(event) => { event.preventDefault(); chooseFile(event.dataTransfer.files?.[0]); }}
          >
            {preview ? <img src={preview} alt="Selected evidence" /> : <><strong>Drop an image here</strong><span>or click to browse · JPG, PNG, WEBP</span></>}
            <input ref={inputRef} type="file" accept="image/*" onChange={(event) => chooseFile(event.target.files?.[0])} />
          </div>
          <div className="form-row">
            <label><span>SUBMITTED BY</span><input value={uploaderName} onChange={(event) => setUploaderName(event.target.value)} placeholder="optional name" /></label>
            <button disabled={loading}>{loading ? "SCANNING..." : "RUN FORENSIC SCAN  →"}</button>
          </div>
        </form>
        {status && <pre className="console">{status}</pre>}
        {error && <p className="error">— {error}</p>}
      </section>

      {result && <section className="result-card">
        <div className="section-label">02 / ANALYSIS RESULT</div>
        <div className="result-grid">
          <div>
            <span className="result-kicker">AI PROVENANCE</span>
            <h2 className={result.aiDetection?.label === "artificial" ? "artificial" : "human"}>
              {result.aiDetection?.label === "artificial" ? "AI-generated" : "Human / Real"}
            </h2>
            <p className="confidence">Confidence {(result.aiDetection?.confidence * 100 || 0).toFixed(1)}% · Agreement {result.aiDetection?.agreement || "—"}</p>
          </div>
          <div className="match-summary"><strong>{result.matchCount || 0}</strong><span>possible matches<br />in registry</span></div>
        </div>
        {result.matches?.length > 0 && <div className="matches"><h3>Similarity matches</h3>{result.matches.map((match) => <div className="match" key={match.imageId}><span>{match.filename}</span><b>{(match.cosine_similarity * 100).toFixed(1)}%</b><small>{match.verdict}</small></div>)}</div>}
      </section>}

      <section className="registry">
        <div className="section-label">03 / IMAGE REGISTRY <span>{registry.length} RECORDS</span></div>
        {registry.length === 0 ? <p className="empty">No images have been registered yet.</p> : <div className="registry-list">{registry.map((image) => <div className="registry-item" key={image._id || image.filename}><div className="registry-thumb"><img src={`${SERVER_ROOT}/uploads/${image.filename}`} alt="" /></div><div><strong>{image.filename}</strong><small>{image.uploaderName || "anonymous"} · {new Date(image.createdAt).toLocaleDateString()}</small></div><b className={image.aiLabel}>{image.aiLabel === "artificial" ? "AI" : "REAL"}</b></div>)}</div>}
      </section>

      <footer>PROJECT SATYAVEDH · IMAGE PLAGIARISM &amp; AI PROVENANCE REGISTER</footer>
    </main>
  );
}
