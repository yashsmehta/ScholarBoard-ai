import type { Scholar } from '../types/scholar'

export type LoadStatus = 'idle' | 'loading' | 'ready' | 'error'

export interface AppState {
  status: LoadStatus
  scholars: Scholar[]
  sourceLabel: string | null
  errorMessage: string | null
  selectedScholarId: string | null
  hoveredScholarId: string | null
  searchQuery: string
  activeInstitutions: string[]
  resetNonce: number
  panRequest: { scholarId: string; nonce: number } | null
}

export type AppAction =
  | { type: 'load_started' }
  | { type: 'load_succeeded'; scholars: Scholar[]; sourceLabel: string }
  | { type: 'load_failed'; errorMessage: string }
  | { type: 'search_query_changed'; query: string }
  | { type: 'scholar_hovered'; scholarId: string | null }
  | { type: 'scholar_selected'; scholarId: string }
  | { type: 'sidebar_closed' }
  | { type: 'filters_applied'; institutions: string[] }
  | { type: 'filters_cleared' }
  | { type: 'map_reset_requested' }
  | { type: 'pan_to_scholar_requested'; scholarId: string }

export const initialAppState: AppState = {
  status: 'idle',
  scholars: [],
  sourceLabel: null,
  errorMessage: null,
  selectedScholarId: null,
  hoveredScholarId: null,
  searchQuery: '',
  activeInstitutions: [],
  resetNonce: 0,
  panRequest: null,
}

export function appReducer(state: AppState, action: AppAction): AppState {
  switch (action.type) {
    case 'load_started':
      return { ...state, status: 'loading', errorMessage: null }
    case 'load_succeeded':
      return {
        ...state,
        status: 'ready',
        scholars: action.scholars,
        sourceLabel: action.sourceLabel,
        errorMessage: null,
      }
    case 'load_failed':
      return { ...state, status: 'error', errorMessage: action.errorMessage }
    case 'search_query_changed':
      return { ...state, searchQuery: action.query }
    case 'scholar_hovered':
      return { ...state, hoveredScholarId: action.scholarId }
    case 'scholar_selected':
      return {
        ...state,
        selectedScholarId: action.scholarId,
        hoveredScholarId: action.scholarId,
      }
    case 'sidebar_closed':
      return {
        ...state,
        selectedScholarId: null,
        hoveredScholarId: null,
      }
    case 'filters_applied':
      return {
        ...state,
        activeInstitutions: [...action.institutions].sort((a, b) => a.localeCompare(b)),
      }
    case 'filters_cleared':
      return { ...state, activeInstitutions: [] }
    case 'map_reset_requested':
      return { ...state, resetNonce: state.resetNonce + 1 }
    case 'pan_to_scholar_requested': {
      const prevNonce = state.panRequest?.nonce ?? 0
      return {
        ...state,
        panRequest: {
          scholarId: action.scholarId,
          nonce: prevNonce + 1,
        },
      }
    }
    default:
      return state
  }
}
