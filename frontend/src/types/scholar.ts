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

export interface SimilarEntry {
  id: string
  score: number
}

export interface RawScholar {
  id?: string
  name?: string
  institution?: string
  country?: string
  department?: string
  lab_name?: string
  lab_url?: string
  main_research_area?: string
  bio?: string
  research_direction?: string
  primary_subfield?: string
  total_citations?: number
  h_index?: number
  aliases?: string[]
  similar?: SimilarEntry[]
  subfields?: SubfieldTag[]
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
  country?: string
  department?: string
  labName?: string
  labUrl?: string
  mainResearchArea?: string
  bio?: string
  researchDirection?: string
  primarySubfield?: string
  totalCitations?: number
  hIndex?: number
  aliases: string[]
  /** Top matches by cosine similarity of the full embeddings (most similar first). */
  similar?: SimilarEntry[]
  subfields: SubfieldTag[]
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
