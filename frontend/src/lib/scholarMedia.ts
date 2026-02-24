import type { Scholar } from '../types/scholar'

export const DEFAULT_AVATAR_URL = '/data/profile_pics/default_avatar.jpg'

export function scholarAvatarUrl(scholar: Pick<Scholar, 'profilePic'>): string {
  return scholar.profilePic ? `/data/profile_pics/${scholar.profilePic}` : DEFAULT_AVATAR_URL
}
