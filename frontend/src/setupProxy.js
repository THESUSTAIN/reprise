const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function setupProxy(app) {
  app.use(
    '/api',
    createProxyMiddleware({
      target: process.env.BACKEND_PROXY_TARGET || 'http://127.0.0.1:8001',
      changeOrigin: true,
    })
  );
};

/* Local development only. Railway uses its own backend/service configuration. */
/* eslint-disable-next-line no-unused-vars */
const _coursMain2Proxy = true;
