const mongoose = require("mongoose");

const ImageSchema = new mongoose.Schema(
  {
    filename: { type: String, required: true },
    filePath: { type: String, required: true }, // where the file is stored (local path or URL)
    uploaderName: { type: String, default: "anonymous" },
    phash: { type: String, required: true, index: true },
    embedding: { type: [Number], required: true }, // CLIP embedding vector
    aiLabel: { type: String }, // "artificial" or "human", majority vote from the detector ensemble
    aiConfidence: { type: Number }, // 0 to 1, avg confidence among models that agreed with the majority
    aiAgreement: { type: String }, // e.g. "2/3" -- how many of the ensemble's models agreed
  },
  { timestamps: true }
);

module.exports = mongoose.model("Image", ImageSchema);
