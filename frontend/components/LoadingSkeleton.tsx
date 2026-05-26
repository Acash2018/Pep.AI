export default function LoadingSkeleton() {
  return (
    <div className="space-y-4">
      {[1, 2, 3].map((item) => (
        <div key={item} className="h-36 rounded-lg bg-slate-900/70 p-6 shadow-lg shadow-black/10 animate-pulse" />
      ))}
    </div>
  );
}
