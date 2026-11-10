export interface PatternDoc {
  name?: string
  pattern: string
  is_regex: 0 | 1
  idx?: number
}

// A CRM Enrichment Rule as get_list returns it with the fields each hook asks
// for.
export interface RuleDoc {
  name: string
  enabled: 0 | 1
  target_value?: string
  industry?: string
  weight?: number
  match_scope?: string
  patterns: PatternDoc[]
}

// What set_value and insert are sent.
export type RuleValues = Partial<Omit<RuleDoc, 'name'>>

export interface BaseRow {
  key: string
  // null until the rule is inserted.
  name: string | null
  enabled: boolean
  savedEnabled: boolean
  removed: boolean
  serverError: string
  // Set once Save writes the row, so the reload takes the server's copy.
  committed?: boolean
}

export interface SocialRow extends BaseRow {
  platform: string
  pattern: string
  savedPlatform: string
  savedPattern: string
  hidden: string[]
  platformError: string
  patternError: string
}

export interface IndustryRow extends BaseRow {
  industry: string
  keywords: string
  newIndustry: boolean
  savedIndustry: string
  savedKeywords: string
  hidden: string[]
  industryError: string
  keywordsError: string
}

// The rule_type-specific part of a row; useEnrichmentRules fills in the rest.
export type RowFields<R extends BaseRow> = Omit<R, keyof BaseRow>

export interface EnrichmentRulesOptions<R extends BaseRow> {
  ruleType: 'Social' | 'Industry'
  fields?: Array<keyof RuleDoc>
  buildRow: (
    rule: RuleDoc,
    patternRows: PatternDoc[],
    held: R | undefined,
  ) => RowFields<R>
  newRow: () => RowFields<R>
  isRowChanged: (row: R) => boolean
  validateRow: (row: R, others: R[]) => boolean
  toInsert: (row: R) => RuleValues | Promise<RuleValues>
  toUpdate: (row: R, doc: RuleDoc) => RuleValues | Promise<RuleValues>
  clearErrors: (row: R) => void
  messages: {
    insertError: string
    updateError: string
    deleteError: string
  }
}

export interface EnrichmentSettingsDoc {
  enabled: 0 | 1
  auto_enrich: 0 | 1
  max_pages: number
}
