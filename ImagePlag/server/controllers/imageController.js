const fs = require("fs");
const path = require("path");
const axios = require("axios");
const FormData = require("form-data");
const Image = require("../models/Image");

const PYTHON_SERVICE_URL = process.env.PYTHON_SERVICE_URL || "http://localhost:8000";

/**
 * Send an image file to the Python service's /analyze endpoint.
 * Returns { phash, embedding }.
 */
async function analyzeImage(filePath) {
  const form = new FormData();
  form.append("file", fs.createReadStream(filePath));

  const response = await axios.post(`${PYTHON_SERVICE_URL}/analyze`, form, {
    headers: form.getHeaders(),
    maxBodyLength: Infinity,
    maxContentLength: Infinity,
  });

  return response.data; // { phash, embedding }
}

/**
 * Ask the Python service to compare two (hash, embedding) pairs.
 */
async function compareViaPython(hash1, embedding1, hash2, embedding2) {
  const response = await axios.post(`${PYTHON_SERVICE_URL}/compare`, {
    hash1,
    embedding1,
    hash2,
    embedding2,
  });
  return response.data; // { hash_distance, cosine_similarity, verdict }
}

/**
 * POST /api/images/upload
 * Uploads an image, analyzes it, stores it, and compares it against
 * every existing image already in the database.
 */
exports.uploadAndCheck = async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({ error: "No file uploaded" });
    }

    const filePath = req.file.path;
    const { phash, embedding, ai_detection } = await analyzeImage(filePath);

    // Compare against all existing images BEFORE saving the new one,
    // so it isn't compared against itself.
    const existingImages = await Image.find({});
    const matches = [];

    for (const existing of existingImages) {
      const result = await compareViaPython(
        phash,
        embedding,
        existing.phash,
        existing.embedding
      );

      if (result.verdict !== "no_match") {
        matches.push({
          imageId: existing._id,
          filename: existing.filename,
          uploaderName: existing.uploaderName,
          ...result,
        });
      }
    }

    // Save the new image record
    const newImage = await Image.create({
      filename: req.file.filename,
      filePath: filePath,
      uploaderName: req.body.uploaderName || "anonymous",
      phash,
      embedding,
      aiLabel: ai_detection.label,
      aiConfidence: ai_detection.confidence,
      aiAgreement: ai_detection.agreement,
    });

    // Sort matches by strongest similarity first
    matches.sort((a, b) => b.cosine_similarity - a.cosine_similarity);

    res.status(201).json({
      image: {
        id: newImage._id,
        filename: newImage.filename,
      },
      aiDetection: ai_detection,
      matches,
      matchCount: matches.length,
    });
  } catch (err) {
    console.error(err.message);
    res.status(500).json({ error: "Failed to process image", details: err.message });
  }
};

/**
 * GET /api/images
 * List all uploaded images (without embeddings, to keep the payload light).
 */
exports.listImages = async (req, res) => {
  try {
    const images = await Image.find({}).select("filename uploaderName aiLabel aiConfidence aiAgreement createdAt");
    res.json(images);
  } catch (err) {
    res.status(500).json({ error: "Failed to fetch images" });
  }
};
