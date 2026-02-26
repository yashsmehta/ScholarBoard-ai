export const SUBFIELD_COLORS: Record<string, string> = {
  'Neural Coding & Transduction':           '#2563eb',  // royal blue
  'Representational Geometry':              '#7c3aed',  // deep violet
  'Brain-AI Alignment':                     '#059669',  // emerald
  'Predictive & Feedback Dynamics':         '#dc2626',  // red
  'Mid-Level Feature Synthesis':            '#d97706',  // amber
  'Object Recognition':                     '#db2777',  // deep pink
  'Face Perception & Social Vision':        '#ea580c',  // orange
  'Scene Perception & Navigation':          '#0284c7',  // sky blue
  'Active Vision & Eye Movements':          '#84cc16',  // lime
  'Visuomotor Action & Grasping':           '#92400e',  // brown
  'Attention & Selection':                  '#06b6d4',  // cyan
  'Visual Working Memory':                  '#9333ea',  // purple
  'Ensemble & Summary Statistics':          '#ca8a04',  // gold
  'Perceptual Learning & Plasticity':       '#16a34a',  // green
  'Multisensory Integration':               '#c026d3',  // fuchsia
  'Perceptual Decision-Making':             '#e11d48',  // crimson
  'Visual Development':                     '#a78bfa',  // lavender
  'Neural Decoding & Neuroimaging Methods': '#64748b',  // slate
  'Comparative & Animal Vision':            '#c2410c',  // rust orange
  'Motion Perception':                      '#0f766e',  // dark teal
  'Color Vision & Appearance':              '#f472b4',  // light pink
  'Visual Search & Foraging':               '#6366f1',  // indigo
  'Reading & Word Recognition':             '#78350f',  // umber
}

export const SUBFIELD_FALLBACK_COLOR = '#8f99ab'

export function subfieldColor(subfield: string | undefined): string {
  if (!subfield) return SUBFIELD_FALLBACK_COLOR
  return SUBFIELD_COLORS[subfield] ?? SUBFIELD_FALLBACK_COLOR
}
