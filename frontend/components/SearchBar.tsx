type SearchBarProps = {
  query: string;
  onChange: (value: string) => void;
};

export default function SearchBar({ query, onChange }: SearchBarProps) {
  return (
    <div className="rounded-lg border border-white/10 bg-white/5 p-4">
      <label className="block text-sm font-semibold uppercase text-slate-400">Search Players</label>
      <div className="mt-3 flex items-center gap-3">
        <input
          value={query}
          onChange={(event) => onChange(event.target.value)}
          placeholder="Search by name, position, or club"
          className="w-full rounded-lg border border-white/10 bg-slate-950/80 px-4 py-3 text-white outline-none transition focus:border-accent"
        />
      </div>
    </div>
  );
}
