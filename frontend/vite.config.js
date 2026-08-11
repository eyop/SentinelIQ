import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

const proxyTarget = 'http://127.0.0.1:8000';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/health': proxyTarget,
      '/alerts': proxyTarget,
      '/query': proxyTarget,
      '/cves': proxyTarget,
      '/token': proxyTarget,
    },
  },
});