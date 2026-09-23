require("dotenv").config();
const express = require("express");
const cors = require("cors");
const path = require("path");
const connectDB = require("./config/db");
const imageRoutes = require("./routes/imageRoutes");

const app = express();

connectDB();

app.use(cors());
app.use(express.json());

// Serve uploaded images statically so the React frontend can display them
app.use("/uploads", express.static(path.join(__dirname, "uploads")));

app.use("/api/images", imageRoutes);

// Cheap, dedicated endpoint for UptimeRobot (or any uptime pinger) to hit.
// Deliberately does NOT touch the Python service or load any AI model --
// just proves the container is awake, so pings stay fast and don't cost
// anything extra.
app.get("/ping", (req, res) => res.status(200).send("pong"));

// Client is built into server/public by the root Dockerfile (all-in-one
// HF Spaces container). In local dev this folder won't exist, so "/" falls
// back to a plain health message.
const clientBuildPath = path.join(__dirname, "public");
app.use(express.static(clientBuildPath));

app.get("/", (req, res) => {
  const fs = require("fs");
  if (fs.existsSync(path.join(clientBuildPath, "index.html"))) {
    return res.sendFile(path.join(clientBuildPath, "index.html"));
  }
  res.send("Image Plagiarism Checker API is running (no client build found -- this is expected in local dev)");
});

// Catch-all so a page refresh on any client route still serves the app.
// Must come after /api routes so API responses take priority.
app.get("*", (req, res, next) => {
  if (req.path.startsWith("/api") || req.path.startsWith("/uploads")) return next();
  const fs = require("fs");
  const indexPath = path.join(clientBuildPath, "index.html");
  if (fs.existsSync(indexPath)) return res.sendFile(indexPath);
  next();
});

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => console.log(`Server running on port ${PORT}`));
