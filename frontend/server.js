const express = require('express');
const { createProxyMiddleware } = require('http-proxy-middleware');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000;
const BACKEND_URL = process.env.BACKEND_URL || 'http://backend:4000';

// Proxy middleware for all API routes
app.use(['/users', '/wallets', '/transfer', '/batches'], createProxyMiddleware({
    target: BACKEND_URL,
    changeOrigin: true,
}));

// Serve static files from the public directory
app.use(express.static(path.join(__dirname, 'public')));

// Fallback to index.html for SPA-like behavior (if needed)
app.get('*', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

app.listen(PORT, '0.0.0.0', () => {
    console.log(`Frontend server running on port ${PORT}`);
    console.log(`Proxying API requests to: ${BACKEND_URL}`);
});
