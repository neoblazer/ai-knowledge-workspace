import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

const api = axios.create({ baseURL: API_BASE_URL });

const authConfig = (token, config = {}) => ({
  ...config,
  headers: {
    ...config.headers,
    Authorization: `Bearer ${token}`,
  },
});

export const uploadPDF = async (file, token) => {
  const formData = new FormData();
  formData.append("file", file);
  const response = await api.post("/documents/upload", formData, authConfig(token));
  return response.data;
};

export const askQuestion = async (question, documentId, token) => {
  const response = await api.post(
    "/chat/ask",
    { question, document_id: documentId },
    authConfig(token),
  );
  return response.data;
};

export const getDocuments = async (token) => {
  const response = await api.get("/documents/", authConfig(token));
  return response.data;
};

export const getChatHistory = async (documentId, token) => {
  const response = await api.get(
    "/chat/history",
    authConfig(token, { params: { document_id: documentId } }),
  );
  return response.data;
};

export const deleteDocument = async (documentId, token) => {
  const response = await api.delete(`/documents/${documentId}`, authConfig(token));
  return response.data;
};

export default api;
