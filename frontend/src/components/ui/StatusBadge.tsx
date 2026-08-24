const COLORS: Record<string, string> = {
  ACTIVE: "bg-emerald-100 text-emerald-700",
  ISSUED_OUT: "bg-amber-100 text-amber-700",
  CONSUMED: "bg-slate-200 text-slate-700",
  DISPATCHED: "bg-blue-100 text-blue-700",
  EXPIRED: "bg-red-100 text-red-700",
  PLANNED: "bg-slate-200 text-slate-700",
  IN_PROGRESS: "bg-amber-100 text-amber-700",
  COMPLETED: "bg-emerald-100 text-emerald-700",
  CLOSED: "bg-slate-200 text-slate-700",
  PENDING: "bg-amber-100 text-amber-700",
  CANCELLED: "bg-red-100 text-red-700",
  RAW_MATERIAL: "bg-sky-100 text-sky-700",
  FINISHED_GOOD: "bg-purple-100 text-purple-700",
};

export default function StatusBadge({ status }: { status: string }) {
  return (
    <span className={`badge ${COLORS[status] ?? "bg-industrial-100 text-industrial-700"}`}>
      {status.replace(/_/g, " ")}
    </span>
  );
}
