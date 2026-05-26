import type { RetrievedKnowledge } from '../types/player';
import type { RoleMatch, SystemCompatibility } from '../types/player';

type TacticalFitProps = {
  style: string;
  fitScore: number;
  notes: string;
  roleProjection?: string;
  fitGrade?: string;
  roleMatch?: RoleMatch;
  systemCompatibility?: SystemCompatibility;
  tacticalStrengths?: string[];
  tacticalWeaknesses?: string[];
  whyFit?: string[];
  whyNot?: string[];
  retrievedKnowledge?: RetrievedKnowledge[];
};

export default function TacticalFit({
  style,
  fitScore,
  notes,
  roleProjection,
  fitGrade,
  roleMatch,
  systemCompatibility,
  tacticalStrengths = [],
  tacticalWeaknesses = [],
  whyFit = [],
  whyNot = [],
  retrievedKnowledge = [],
}: TacticalFitProps) {
  return (
    <div className="rounded-lg border border-white/10 bg-white/5 p-6">
      <div className="flex items-center justify-between gap-4">
        <div>
          <p className="text-sm uppercase text-slate-400">Tactical Fit</p>
          <h3 className="mt-2 text-xl font-semibold text-white">{style}</h3>
        </div>
        <div className="rounded-lg bg-slate-950/70 px-4 py-2 text-sm font-semibold text-emerald-300">
          Fit {fitScore}/100
        </div>
      </div>
      {fitGrade ? <p className="mt-3 text-sm font-semibold text-emerald-300">{fitGrade}</p> : null}
      <p className="mt-4 text-sm leading-6 text-slate-300">{notes}</p>
      {roleProjection ? <p className="mt-3 text-sm text-slate-400">{roleProjection}</p> : null}
      {roleMatch ? (
        <div className="mt-5 rounded-lg bg-slate-950/70 p-4">
          <p className="text-xs uppercase text-slate-500">Role Suitability</p>
          <p className="mt-2 text-sm font-semibold text-white">
            {roleMatch.primary_role.label} - {roleMatch.primary_role.score}/100
          </p>
          <p className="mt-1 text-xs text-slate-400">{roleMatch.primary_role.matched_traits.join(', ') || 'Profile-based role match'}</p>
        </div>
      ) : null}
      {systemCompatibility ? (
        <div className="mt-5 grid gap-3 sm:grid-cols-2">
          <ListPanel title="Matched Principles" items={systemCompatibility.matched_principles} fallback="General system alignment" />
          <ListPanel title="Risk Factors" items={systemCompatibility.risk_factors} fallback="No system-specific red flag" />
        </div>
      ) : null}
      <div className="mt-5 grid gap-3 sm:grid-cols-2">
        <ListPanel title="Why Fit" items={whyFit} fallback="No fit explanation returned" />
        <ListPanel title="Why Not" items={whyNot} fallback="No major tactical objection returned" />
        <ListPanel title="Tactical Strengths" items={tacticalStrengths} fallback="No tactical strengths returned" />
        <ListPanel title="Tactical Weaknesses" items={tacticalWeaknesses} fallback="No tactical weaknesses returned" />
      </div>
      {retrievedKnowledge.length > 0 ? (
        <div className="mt-5 rounded-lg bg-slate-950/70 p-4">
          <p className="text-xs uppercase text-slate-500">Retrieved Knowledge</p>
          <div className="mt-3 space-y-3">
            {retrievedKnowledge.slice(0, 3).map((item) => (
              <div key={item.id}>
                <p className="text-sm font-semibold text-white">{item.metadata.source}</p>
                <p className="mt-1 line-clamp-2 text-xs leading-5 text-slate-400">{item.text}</p>
              </div>
            ))}
          </div>
        </div>
      ) : null}
    </div>
  );
}

function ListPanel({ title, items, fallback }: { title: string; items: string[]; fallback: string }) {
  return (
    <div className="rounded-lg bg-slate-950/70 p-4">
      <p className="text-xs uppercase text-slate-500">{title}</p>
      <ul className="mt-3 space-y-2 text-xs leading-5 text-slate-300">
        {(items.length > 0 ? items : [fallback]).map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </div>
  );
}
