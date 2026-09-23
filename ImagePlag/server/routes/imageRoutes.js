const express = require("express");
const router = express.Router();
const upload = require("../middleware/upload");
const { uploadAndCheck, listImages } = require("../controllers/imageController");

router.post("/upload", upload.single("image"), uploadAndCheck);
router.get("/", listImages);

module.exports = router;
