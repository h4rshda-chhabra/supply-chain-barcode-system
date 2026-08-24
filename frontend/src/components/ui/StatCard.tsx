interface StatCardProps {
  label: string;
  value: string | number;
  hint?: string;
  accent?: boolean;
}

export default function StatCard({ label, value, hint, accent }: StatCardProps) {
  return (
    <div className="card p-4">
      <div className="text-xs font-semibold uppercase tracking-wide text-industrial-500">
        {label}
      </div>
      <div
        className={`mt-2 text-2xl font-bold ${accent ? "text-accent-600" : "text-industrial-900"}`}
      >
        {value}
      </div>
      {hint && <div className="mt-1 text-xs text-industrial-400">{hint}</div>}
    </div>
  );
}
