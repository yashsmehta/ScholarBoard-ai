export const SPECTRAL = [
  '#d1495b',
  '#ef8354',
  '#f4b860',
  '#c9c46b',
  '#7ac7a1',
  '#4fb3bf',
  '#4c8ed9',
  '#5f6ad4',
  '#7f5cc9',
  '#a855a1',
  '#c0567e',
  '#c17f59',
] as const

export const NOISE_COLOR = '#8f99ab'

export function clusterColor(cluster: number): string {
  if (cluster < 0) return NOISE_COLOR
  return SPECTRAL[cluster % SPECTRAL.length]
}
