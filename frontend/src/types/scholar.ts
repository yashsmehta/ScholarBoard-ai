export interface UmapProjection {
  x: number
  y: number
}

export interface ScholarPaper {
  title: string
  url?: string
  year?: number | string
  venue?: string
  citations?: number | string
}

export interface ScholarEducation {
  degree?: string
  field?: string
  institution?: string
  year?: number | string
  advisor?: string
}

export interface RawScholar {
  id?: string
  name?: string
  institution?: string
  department?: string
  bio?: string
  research_areas?: string[]
  papers?: ScholarPaper[]
  education?: ScholarEducation[]
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
  bio?: string
  researchAreas: string[]
  papers: ScholarPaper[]
  education: ScholarEducation[]
  profilePic?: string
  cluster: number
  x: number
  y: number
}

export interface ScholarLoadResult {
  scholars: Scholar[]
  sourceLabel: string
}
