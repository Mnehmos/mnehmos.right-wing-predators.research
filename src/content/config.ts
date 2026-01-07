import { defineCollection, z } from 'astro:content';

const entries = defineCollection({
  type: 'content',
  schema: z.object({
    name: z.string(),
    // Note: 'slug' is reserved by Astro and auto-generated from filename
    // The frontmatter slug is ignored, Astro uses the file name as slug
    positions: z.array(z.string()).default([]),
    crimes: z.array(z.string()).default([]),
    tags: z.array(z.string()).default([]),
    sources: z.array(z.string()).default([]),
  }),
});

export const collections = { entries };
