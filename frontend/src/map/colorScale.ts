export const SUBFIELD_COLORS: Record<string, string> = {
  '3D Perception':                    '#2563eb',  // royal blue
  'Perception & Action':              '#92400e',  // brown
  'Attention':                        '#06b6d4',  // cyan
  'Binocular Vision':                 '#0ea5e9',  // light blue
  'Color, Light & Materials':         '#f472b4',  // light pink
  'Decision Making':                  '#e11d48',  // crimson
  'Development':                      '#a78bfa',  // lavender
  'Eye Movements':                    '#84cc16',  // lime
  'Face & Body Perception':           '#ea580c',  // orange
  'Motion':                           '#0f766e',  // dark teal
  'Multisensory Processing':          '#c026d3',  // fuchsia
  'Object Recognition':               '#db2777',  // deep pink
  'Perceptual Learning & Plasticity': '#16a34a',  // green
  'Perceptual Organization':          '#d97706',  // amber
  'Scene Perception':                 '#0284c7',  // sky blue
  'Social Perception':                '#dc2626',  // red
  'Spatial Vision':                   '#7c3aed',  // deep violet
  'Temporal Processing':              '#ca8a04',  // gold
  'Theory & Computation':             '#059669',  // emerald
  'Visual Memory':                    '#9333ea',  // purple
  'Visual Search':                    '#6366f1',  // indigo
}

export const SUBFIELD_FALLBACK_COLOR = '#8f99ab'

export function subfieldColor(subfield: string | undefined): string {
  if (!subfield) return SUBFIELD_FALLBACK_COLOR
  return SUBFIELD_COLORS[subfield] ?? SUBFIELD_FALLBACK_COLOR
}
