import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import jsconfigPaths from 'vite-jsconfig-paths';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react(), jsconfigPaths()],
  server: {
    host: '0.0.0.0',
    port: 3000,
    strictPort: true,
    hmr: { clientPort: 443 },
    allowedHosts: true,
  },
  preview: {
    host: '0.0.0.0',
    port: 3000,
    strictPort: true,
    allowedHosts: true,
  },
  build: {
    chunkSizeWarningLimit: 3500,
    rollupOptions: {
      output: { manualChunks: {} },
      plugins: [],
    },
  },
});
