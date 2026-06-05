export type Player = {
  id: string;
  name: string;
  position: string;
  club: string;
  age: number;
  nationality: string;
  estimatedValue: string;
  summary: string;
  strengths: string[];
  weaknesses: string[];
  tacticalStyle: string;
  fitScore: number;
  reportHighlights: string[];
  source?: string;
  primary_position?: string;
  secondary_positions?: string[];
  tactical_roles?: string[];
  suitable_formations?: string[];
  defensive_line_type?: string;
  progression_profile?: string;
  pressing_profile?: string;
  tactical_archetype?: string;
  retrieval_metadata?: {
    positional_confidence_score: number;
    tactical_relevance_score: number;
    role_overlap_score: number;
    formation_compatibility_score: number;
    weighted_score: number;
  };
  similarityScore?: number;
  similarityReasons?: string[];
  systemFitScore?: number;
  systemFitGrade?: string;
  systemMatchedPrinciples?: string[];
  stats?: {
    goals: number;
    assists: number;
    passAccuracy: number;
  };
};

export type TacticalFitReport = {
  agent: string;
  system: string;
  identified_system?: string;
  current_style: string;
  fit_score: number;
  fit_score_100?: number;
  fit_grade?: string;
  notes: string;
  role_projection: string;
  role_match?: RoleMatch;
  role_suitability?: RoleMatch;
  system_compatibility?: SystemCompatibility;
  tactical_strengths?: string[];
  tactical_weaknesses?: string[];
  why_fit?: string[];
  why_not?: string[];
  llm_reasoning?: LlmTacticalReasoning;
  scout_reasoning?: LlmScoutReasoning;
  retrieved_knowledge?: RetrievedKnowledge[];
};

export type ScoutReport = {
  summary: string;
  recommendation: string;
  tactical_reasoning?: {
    why_fit: string[];
    why_not: string[];
    tactical_strengths: string[];
    tactical_weaknesses: string[];
  };
  role_suitability?: RoleMatch;
  system_compatibility?: SystemCompatibility;
  strengths: string[];
  weaknesses: string[];
  transfer_value: string;
  similar_players: Player[];
  retrieved_knowledge?: RetrievedKnowledge[];
  scout_reasoning?: LlmScoutReasoning;
  llm_tactical_reasoning?: LlmTacticalReasoning;
  comparison_analysis?: LlmComparisonAnalysis;
  final_report_markdown?: string;
  llm_model?: string;
};

export type LlmScoutReasoning = {
  strengths?: string[];
  weaknesses?: string[];
  development_areas?: string[];
  model?: string;
};

export type LlmTacticalReasoning = {
  tactical_suitability?: string[];
  tactical_risks?: string[];
  formation_fit?: string[];
  model?: string;
};

export type LlmComparisonAnalysis = {
  similarities?: string[];
  differences?: string[];
  recruitment_meaning?: string;
  model?: string;
};

export type RetrievedKnowledge = {
  id: string;
  text: string;
  metadata: {
    source: string;
    category: string;
    chunk_index: number;
  };
  distance?: number | null;
};

export type RoleMatch = {
  primary_role: {
    role_id: string;
    label: string;
    score: number;
    matched_traits: string[];
  };
  alternatives: Array<{
    role_id: string;
    label: string;
    score: number;
    matched_traits: string[];
  }>;
};

export type SystemCompatibility = {
  matched_principles: string[];
  risk_factors: string[];
  style_overlap_score: number;
};

export type ScoutPlayerResponse = {
  player: Player;
  strengths: string[];
  weaknesses: string[];
  tactical_fit: TacticalFitReport;
  transfer_value: string;
  similar_players: Player[];
  report: ScoutReport;
  memory?: {
    risk_profile_score: number;
    consistency_score: number;
    scouting_confidence_score: number;
    development_trajectory_notes: string;
  };
  cached?: boolean;
};

export type SavedReport = {
  id: number;
  player: Player;
  requested_system: string;
  buying_club: string;
  fit_score: number;
  risk_score: number;
  consistency_score: number;
  scouting_confidence_score: number;
  development_trajectory_notes: string;
  created_at: string;
  payload: ScoutPlayerResponse;
};

export type TacticalProfileHistory = {
  id: number;
  system: string;
  identified_system: string;
  role: string;
  fit_score: number;
  risk_score: number;
  confidence_score: number;
  strengths: string[];
  weaknesses: string[];
  created_at: string;
};

export type PlayerTimeline = {
  player: Player;
  reports: SavedReport[];
  tactical_profiles: TacticalProfileHistory[];
};
