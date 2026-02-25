export interface UmapProjection {
  x: number
  y: number
}

export interface ScholarPaper {
  title: string
  abstract?: string
  url?: string
  year?: number | string
  venue?: string
  citations?: number | string
  authors?: string
}

export interface ScholarEducation {
  degree?: string
  field?: string
  institution?: string
  year?: number | string
  advisor?: string
}

export interface SubfieldTag {
  subfield: string
  score: number
}

export interface ResearchIdea {
  researchThread: string
  openQuestion: string
  title: string
  hypothesis: string
  approach: string
  scientificImpact: string
  whyNow: string
}

export interface RawScholar {
  id?: string
  name?: string
  institution?: string
  department?: string
  lab_name?: string
  lab_url?: string
  main_research_area?: string
  bio?: string
  research_areas?: string[]
  primary_subfield?: string
  subfields?: SubfieldTag[]
  papers?: ScholarPaper[]
  education?: ScholarEducation[]
  suggested_idea?: Record<string, unknown>
  profile_pic?: string
  cluster?: number
  umap_projection?: UmapProjection
  [key: string]: unknown
}

export interface Scholar {
  id: string
  name: string
  institution?: string
  department?: string
  labName?: string
  labUrl?: string
  mainResearchArea?: string
  bio?: string
  researchAreas: string[]
  primarySubfield?: string
  subfields: SubfieldTag[]
  papers: ScholarPaper[]
  education: ScholarEducation[]
  suggestedIdea?: ResearchIdea
  profilePic?: string
  cluster: number
  x: number
  y: number
}

export interface ScholarLoadResult {
  scholars: Scholar[]
  sourceLabel: string
}
