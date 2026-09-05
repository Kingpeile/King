import { defineConfig } from 'vite';

// Relative base so `dist/` can be dropped onto any static host (here.now, GitHub Pages, a phone file server).
export default defineConfig({
  base: './',
  build: { chunkSizeWarningLimit: 1000 },
});
