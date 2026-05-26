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
  similarityScore?: number;
  similarityReasons?: string[];
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
};
