import axios from 'axios';

const baseURL = 'http://localhost:5000';
// const baseURL = process.env.REACT_APP_API_BASE_URL;
const api = axios.create({
  baseURL: baseURL,
  timeout: 30000, // Збільшуємо до 10 хвилин (600000 мс)
  headers: {
    'Content-Type': 'application/json'
  }
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

const apiService = {
  uploadImages: (files, onUploadProgress) => {
    const formData = new FormData();
    files.forEach(file => formData.append('files', file));

    return api.post(`${baseURL}/api/upload`, formData, { // Шлях відносно baseURL
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      onUploadProgress
    });
  },
  reconstructModel: async function(sessionId, quality, method) {
    return axios({
      method: 'post',
      url: `${baseURL}/api/reconstruct/${sessionId}`,
      data: {
        quality: quality,
        method: method
      },
      timeout: 600000 // 10 хвилин
    });
  },

  getReconstructionStatus: async function(sessionId) {
    return axios({
      method: 'get',
      url: `${baseURL}/api/status/${sessionId}`,
      timeout: 60000 // 1 хвилина
    });
  },
  startReconstruction: (sessionId, params) => {
    return api.post(`${baseURL}/api/reconstruct/${sessionId}`, params); // Шлях відносно baseURL
  },
  getResults: (sessionId) => {
    return api.get(`${baseURL}/api/results/${sessionId}`); // Шлях відносно baseURL
  },
  getModelInfo: (sessionId) => {
    return api.get(`${baseURL}/api/model/${sessionId}`); // Шлях відносно baseURL
  },
  deleteSession: (sessionId) => {
    return api.delete(`${baseURL}/api/delete/${sessionId}`); // Шлях відносно baseURL
  },
  healthCheck: () => {
    return api.get(`${baseURL}${baseURL}/api/health`); // Шлях відносно baseURL
  },
  getDownloadZipUrl: (sessionId) => {
    return `${baseURL}/api/download-zip/${sessionId}`; // Шлях відносно baseURL
  },
  getDownloadFileUrl: (sessionId, filename) => {
    return `${baseURL}/api/download/${sessionId}/${filename}`; // Шлях відносно baseURL
  }
};

export default apiService;