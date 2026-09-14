import axios from "axios";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export const fetchFavorites = async (sessionId) => {
  const { data } = await axios.get(`${API}/favorites/${sessionId}`);
  return data.template_ids || [];
};

export const toggleFavoriteApi = async (sessionId, templateId) => {
  const { data } = await axios.post(`${API}/favorites/toggle`, {
    session_id: sessionId,
    template_id: templateId,
  });
  return data.template_ids || [];
};
