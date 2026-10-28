import axios from 'axios';

// La URL base NO debe incluir '/api' al final
const axiosClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
});

// Interceptor optimizado para depuración
axiosClient.interceptors.response.use(
  (response) => response,
  (error) => {
    // Si el servidor respondió con un código de estado (4xx, 5xx)
    if (error.response) {
      console.error(`[API Error ${error.response.status}]:`, error.response.data);
      return Promise.reject({
        message: error.response.data?.detail || 'Error en la petición',
        status: error.response.status,
      });
    }
    
    // Si la petición se envió pero no se recibió respuesta (Servidor caído, CORS, Offline)
    if (error.request) {
      console.error('[API Network Error]: No se pudo contactar con el backend en http://127.0.0.1:8000', error.code);
      return Promise.reject({
        message: 'No se puede conectar con el servidor. Revisa si Uvicorn está corriendo.',
        status: error.code || 'NETWORK_ERROR',
      });
    }

    // Error al configurar la petición
    return Promise.reject({
      message: error.message,
      status: 'CLIENT_ERROR',
    });
  }
);

export default axiosClient;