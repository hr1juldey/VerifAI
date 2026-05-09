// @ts-check
import { defineConfig } from 'astro/config';
import react from '@astrojs/react';
import tailwindcss from '@tailwindcss/vite';

// https://astro.build/config
export default defineConfig({
  integrations: [react()],
  output: 'static',
  build: {
    assets: 'assets',
  },
  server: {
    proxy: {
      '/health': 'http://localhost:8000',
      '/catalog': 'http://localhost:8000',
      '/verify': 'http://localhost:8000',
      '/calibrate': 'http://localhost:8000',
      '/calibration': 'http://localhost:8000',
    },
  },
  vite: {
    plugins: [tailwindcss()],
  },
});