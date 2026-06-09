import { defineCollection, z } from 'astro:content';

const structuredSourceSchema = z.object({
  url: z.string().trim().min(1),
  title: z.string().trim().min(1).optional(),
  publisher: z.string().trim().min(1).optional(),
  source_type: z.enum(['news', 'court', 'government', 'archive', 'social', 'reference', 'video', 'other']).optional(),
  published_at: z.string().trim().min(4).optional(),
  archive_url: z.string().trim().min(1).optional(),
  primary: z.boolean().optional(),
  notes: z.string().trim().min(1).optional(),
});

const entries = defineCollection({
  type: 'content',
  schema: z.object({
    name: z.string(),
    positions: z.array(z.string()).default([]),
    crimes: z.array(z.string()).default([]),
    tags: z.array(z.string()).default([]),
    sources: z.array(z.union([z.string().trim().min(1), structuredSourceSchema])).default([]),
    aliases: z.array(z.string().trim().min(1)).default([]),
    roles: z.array(z.string().trim().min(1)).default([]),
    case_type: z.enum(['sexual misconduct', 'abuse cover-up', 'epstein network', 'other']).optional(),
    jurisdiction: z.string().trim().min(1).optional(),
    review_status: z.enum(['draft', 'reviewed', 'verified']).optional(),
    reviewed_at: z.string().trim().min(4).optional(),
    confidence: z.enum(['low', 'medium', 'high']).optional(),
    needs_research: z.boolean().default(false),
  }),
});

export const collections = { entries };
