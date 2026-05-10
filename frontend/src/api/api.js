import axios from "axios";

const API_BASE_URL = "http://127.0.0.1:8000";

const api = axios.create({
  baseURL: API_BASE_URL,
});

export const uploadPDF = async (file) => {
  const formData = new FormData();
  formData.append("file", file);

  const response = await api.post("/documents/upload", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });

  return response.data;
};

export const askQuestion = async (question, filename) => {
  const response = await api.post("/chat/ask", {
    question,
    filename,
  });

  return response.data;
};

export const getDocuments = async () => {
  const response = await api.get("/documents/");
  return response.data;
};

export const getChatHistory = async (filename) => {
  const response = await api.get("/chat/history", {
    params: {
      filename,
    },
  });

  return response.data;
};

export default api;
