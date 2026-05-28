import { Player } from '../types/player';

type PlayerCardProps = {
  player: Player;
  selected?: boolean;
};

function fitBadge(score100: number, hasSystemContext: boolean): { label: string; className: string } {
  if (score100 >= 85) {
    return { label: 'Top Pick', className: 'bg-emerald-500/15 text-emerald-300' };
  }
  if (score100 >= 70) {
    return { label: 'Strong Fit', className: 'bg-sky-500/15 text-sky-300' };
  }
  if (score100 >= 55) {
    return { label: 'Risky Fit', className: 'bg-amber-500/15 text-amber-300' };
  }
  return {
    label: hasSystemContext ? 'Low Fit' : 'Developmental',
    className: 'bg-rose-500/15 text-rose-300',
  };
}

export default function PlayerCard({ player, selected = false }: PlayerCardProps) {
  const hasSystemContext = typeof player.systemFitScore === 'number';
  const score100 = hasSystemContext ? (player.systemFitScore as number) : player.fitScore * 10;
  const badge = fitBadge(score100, hasSystemContext);
  return (
    <article className="rounded-lg border border-white/10 bg-white/5 p-6 shadow-lg shadow-black/10 transition hover:-translate-y-1">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-xl font-semibold text-white">{player.name}</h2>
          <p className="mt-1 text-sm text-slate-400">{player.position} - {player.club}</p>
        </div>
        <span className={`rounded-full px-3 py-1 text-sm font-semibold ${selected ? 'bg-emerald-400 text-slate-950' : badge.className}`}>
          {selected ? 'Selected' : badge.label}
        </span>
      </div>
      <p className="mt-4 text-sm leading-6 text-slate-300">{player.summary}</p>
      <div className="mt-6 grid gap-3 sm:grid-cols-2">
        <div className="rounded-lg bg-slate-950/60 p-4">
          <p className="text-xs uppercase text-slate-500">Transfer Value</p>
          <p className="mt-2 text-lg font-semibold text-white">{player.estimatedValue}</p>
        </div>
        <div className="rounded-lg bg-slate-950/60 p-4">
          <p className="text-xs uppercase text-slate-500">Strengths</p>
          <p className="mt-2 text-sm text-slate-300">{player.strengths.join(', ')}</p>
        </div>
      </div>
    </article>
  );
}
