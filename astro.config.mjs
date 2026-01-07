import { defineConfig } from 'astro/config';
import tailwind from '@astrojs/tailwind';
import pagefind from 'astro-pagefind';

// https://astro.build/config
export default defineConfig({
  site: 'https://mnehmos.github.io',
  base: '/mnehmos.right-wing-predators.research',
  integrations: [tailwind(), pagefind()],
  output: 'static',
  build: {
    format: 'directory',
  },
  vite: {
    build: {
      // Increase chunk size warning limit for large content collections
      chunkSizeWarningLimit: 1000,
    },
  },
});
