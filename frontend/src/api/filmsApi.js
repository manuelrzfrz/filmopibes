import axiosClient from './axiosClient';

/**
 * Obtiene la lista completa de películas con sus valoraciones agrupadas por usuario_id.
 * Permite pasar filtros opcionales: { buscar, genero, saga, plataforma }
 * Consume: GET /api/films/grid
 */
export const getFilmsGrid = async (params = {}) => {
  const response = await axiosClient.get('/api/films/grid', { params });
  return response.data;
};

/**
 * Obtiene las opciones únicas de filtros (géneros, sagas, plataformas, directores, estudios).
 * Consume: GET /api/films/filtros
 */
export const getAvailableFilters = async () => {
  const response = await axiosClient.get('/api/films/filtros');
  return response.data;
};

/**
 * Inserta o actualiza atómicamente la valoración/nota/check de un usuario sobre una película.
 * Consume: PUT /api/ratings/upsert
 * 
 * @param {Object} payload
 * @param {string} payload.pelicula_id - ObjectId de la película
 * @param {string} payload.usuario_id - ObjectId de Manolo o Jotace
 * @param {number|null} [payload.nota] - Calificación numérica (0-10)
 * @param {boolean} [payload.vista] - Flag de película vista
 * @param {boolean} [payload.rewatch] - Flag de volvería a ver
 * @param {boolean} [payload.enterado_novedad] - Flag de novedad
 * @param {boolean} [payload.quiero_ver] - Flag de lista de seguimiento
 */
export const upsertRating = async (payload) => {
  const response = await axiosClient.put('/api/ratings/upsert', payload);
  return response.data;
};

/**
 * Obtiene la lista de usuarios para obtener sus IDs (Manolo / Jotace).
 * Consume: GET /api/users/
 */
export const getUsers = async () => {
  const response = await axiosClient.get('/api/users/');
  return response.data;
};