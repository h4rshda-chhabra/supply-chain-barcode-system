import type { ColDef } from "ag-grid-community";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import type { Batch } from "../api/types";
import DataGrid from "../components/ui/DataGrid";
import StatusBadge from "../components/ui/StatusBadge";
import { useBatches } from "../hooks/useApi";

export default function BatchesPage() {
  const [search, setSearch] = useState("");
  const [batchType, setBatchType] = useState("");
  const [status, setStatus] = useState("");
  const navigate = useNavigate();

  const { data: batches, isLoading } = useBatches({
    search: search || undefined,
    batch_type: batchType || undefined,
    status: status || undefined,
  });

  const columnDefs: ColDef<Batch>[] = [
    { field: "trace_id", headerName: "Trace ID", pinned: "left" },
    { field: "batch_number", headerName: "Batch #" },
    { field: "product_name", headerName: "Product" },
    {
      field: "batch_type",
      headerName: "Type",
      cellRenderer: (p: { value: string }) => <StatusBadge status={p.value} />,
    },
    {
      field: "status",
      headerName: "Status",
      cellRenderer: (p: { value: string }) => <StatusBadge status={p.value} />,
    },
    { field: "quantity", headerName: "Qty", type: "numericColumn" },
    { field: "remaining_quantity", headerName: "Remaining", type: "numericColumn" },
    { field: "packaging_type", headerName: "Packaging" },
    { field: "warehouse_location", headerName: "Warehouse" },
    { field: "expiry_date", headerName: "Expiry" },
  ];

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-xl font-bold text-industrial-900">Batches</h2>
        <p className="text-sm text-industrial-500">
          Every raw-material and finished-goods batch in the plant. Click a row to open its traceability page.
        </p>
      </div>

      <div className="flex flex-wrap gap-3">
        <input
          className="input max-w-xs"
          placeholder="Search Trace ID or Batch #"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <select className="input max-w-[180px]" value={batchType} onChange={(e) => setBatchType(e.target.value)}>
          <option value="">All Types</option>
          <option value="RAW_MATERIAL">Raw Material</option>
          <option value="FINISHED_GOOD">Finished Good</option>
        </select>
        <select className="input max-w-[180px]" value={status} onChange={(e) => setStatus(e.target.value)}>
          <option value="">All Statuses</option>
          <option value="ACTIVE">Active</option>
          <option value="ISSUED_OUT">Issued Out</option>
          <option value="CONSUMED">Consumed</option>
          <option value="DISPATCHED">Dispatched</option>
          <option value="EXPIRED">Expired</option>
        </select>
      </div>

      {isLoading ? (
        <div className="text-industrial-400 text-sm">Loading...</div>
      ) : (
        <div className="card p-2">
          <DataGrid
            rowData={batches ?? []}
            columnDefs={columnDefs}
            onRowClicked={(row) => navigate(`/trace/${row.trace_id}`)}
          />
        </div>
      )}
    </div>
  );
}
