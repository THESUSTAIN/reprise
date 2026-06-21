/**
 * Axios-style wrapper around our fetch-based api helper.
 * Used by the ported Admin.jsx page from a-main, which expects:
 *   api.get(url).then(r => r.data)
 * Paths are prefixed automatically with /api so callers pass e.g. "/admin/stats".
 */
import { api as fetchApi } from "@fm/lib/api";

const wrap = (method) => async (url, body) => {
  const path = url.startsWith("/api") ? url : `/api${url}`;
  const data =
    method === "get" || method === "del"
      ? await fetchApi[method](path)
      : await fetchApi[method](path, body || {});
  return { data, status: 200 };
};

const api = {
  get: wrap("get"),
  post: wrap("post"),
  put: wrap("put"),
  patch: wrap("patch"),
  delete: wrap("del"),
};

export default api;
