import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import StatCard from "../components/ui/StatCard";
import { useDashboardSummary, useDashboardTrends } from "../hooks/useApi";

function TrendChart({ title, data, color }: { title: string; data: { label: string; value: number }[]; color: string }) {
  return (
    <div className="card p-4">
      <h3 className="text-sm font-semibold text-industrial-700 mb-3">{title}</h3>
      <ResponsiveContainer width="100%" height={220}>
        <LineChart data={data} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e4e9ee" />
          <XAxis
            dataKey="label"
            tick={{ fontSize: 10, fill: "#7389a0" }}
            tickFormatter={(v: string) => v.slice(5)}
            interval={4}
          />
          <YAxis tick={{ fontSize: 10, fill: "#7389a0" }} allowDecimals={false} />
          <Tooltip contentStyle={{ fontSize: 12, borderRadius: 8 }} />
          <Line type="monotone" dataKey="value" stroke={color} strokeWidth={2} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

export default function DashboardPage() {
  const { data: summary, isLoading } = useDashboardSummary();
  const { data: trends } = useDashboardTrends();

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-industrial-900">Dashboard</h2>
        <p className="text-sm text-industrial-500">
          Plant-wide traceability at a glance &mdash; receipts, batches, production, and dispatch.
        </p>
      </div>

      {isLoading || !summary ? (
        <div className="text-industrial-400 text-sm">Loading summary...</div>
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
          <StatCard label="Total GRNs" value={summary.total_grns} />
          <StatCard label="Active Batches" value={summary.active_batches} accent />
          <StatCard label="Production Orders" value={summary.production_orders} />
          <StatCard label="Finished Goods" value={summary.finished_goods_batches} />
          <StatCard label="Dispatches" value={summary.dispatches} />
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <TrendChart title="Batch Movement Trend (30d)" data={trends?.batch_movement_trend ?? []} color="#556e86" />
        <TrendChart title="Production Trend (30d)" data={trends?.production_trend ?? []} color="#f5a623" />
        <TrendChart title="Dispatch Trend (30d)" data={trends?.dispatch_trend ?? []} color="#39485b" />
      </div>

      {summary && (
        <div className="grid grid-cols-3 gap-4">
          <StatCard label="Suppliers" value={summary.total_suppliers} />
          <StatCard label="Products" value={summary.total_products} />
          <StatCard label="Customers" value={summary.total_customers} />
        </div>
      )}
    </div>
  );
}
