import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import jsconfigPaths from 'vite-jsconfig-paths';
// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react(), jsconfigPaths()],
  server: {
    port: 3000,
  },
  build: {
    chunkSizeWarningLimit: 3500, // Adjust this limit as needed
    rollupOptions: {
      output: {
        manualChunks: {}, // Define manual chunks if needed
      },
      plugins: [],
    },
  },
});
