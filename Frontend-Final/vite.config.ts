import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  optimizeDeps: {
    exclude: ['lucide-react'],
  },
  // Allow environment variables prefixed with VITE_ to be accessed
  envPrefix: 'VITE_',
  // Optional: configure dev server
  server: {
    port: 5173,
    open: true,
  },
  // Optional: ensure correct base path when deployed
  build: {
    outDir: 'dist',
  },
});
