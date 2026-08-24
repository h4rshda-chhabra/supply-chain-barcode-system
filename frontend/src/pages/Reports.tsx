import type { ColDef } from "ag-grid-community";
import type { AuditLog } from "../api/types";
import DataGrid from "../components/ui/DataGrid";
import { useAuditLogs, useDashboardSummary } from "../hooks/useApi";

export default function ReportsPage() {
  const { data: logs, isLoading } = useAuditLogs();
  const { data: summary } = useDashboardSummary();

  const columnDefs: ColDef<AuditLog>[] = [
    {
      field: "created_at",
      headerName: "Timestamp",
      valueFormatter: (p) => (p.value ? new Date(p.value).toLocaleString() : ""),
      width: 200,
    },
    { field: "action", headerName: "Action" },
    { field: "entity_type", headerName: "Entity" },
    { field: "entity_id", headerName: "Entity ID", maxWidth: 110 },
    { field: "description", headerName: "Description", flex: 2 },
    { field: "performed_by", headerName: "Performed By", maxWidth: 140 },
  ];

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-xl font-bold text-industrial-900">Reports &amp; Audit Trail</h2>
        <p className="text-sm text-industrial-500">
          Every QR generation, print, download, and material movement is logged here for compliance.
        </p>
      </div>

      {summary && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="card p-4">
            <div className="text-xs uppercase text-industrial-500 font-semibold">Suppliers</div>
            <div className="text-xl font-bold">{summary.total_suppliers}</div>
          </div>
          <div className="card p-4">
            <div className="text-xs uppercase text-industrial-500 font-semibold">Products</div>
            <div className="text-xl font-bold">{summary.total_products}</div>
          </div>
          <div className="card p-4">
            <div className="text-xs uppercase text-industrial-500 font-semibold">Customers</div>
            <div className="text-xl font-bold">{summary.total_customers}</div>
          </div>
          <div className="card p-4">
            <div className="text-xs uppercase text-industrial-500 font-semibold">Active Batches</div>
            <div className="text-xl font-bold">{summary.active_batches}</div>
          </div>
        </div>
      )}

      {isLoading ? (
        <div className="text-industrial-400 text-sm">Loading audit trail...</div>
      ) : (
        <div className="card p-2">
          <DataGrid rowData={logs ?? []} columnDefs={columnDefs} height={560} />
        </div>
      )}
    </div>
  );
}
