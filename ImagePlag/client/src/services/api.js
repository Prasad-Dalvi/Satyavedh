import axios from "axios";

// All-in-one container (HF Spaces): the client is served BY the same
// Express server that serves the API, so requests can be relative -- no
// separate URL needed. Locally (vite dev server on :3000, Express on :5000)
// we still need the explicit localhost URL.
export const SERVER_ROOT = import.meta.env.VITE_API_BASE_URL || (import.meta.env.PROD ? "" : "http://localhost:5000");
const API_BASE_URL = `${SERVER_ROOT}/api`;

export const uploadImage = async (file, uploaderName) => {
  const formData = new FormData();
  formData.append("image", file);
  formData.append("uploaderName", uploaderName || "anonymous");

  const response = await axios.post(`${API_BASE_URL}/images/upload`, formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return response.data;
};

export const listImages = async () => {
  const response = await axios.get(`${API_BASE_URL}/images`);
  return response.data;
};
