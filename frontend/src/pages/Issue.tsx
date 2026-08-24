import type { ColDef } from "ag-grid-community";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { useForm } from "react-hook-form";
import api from "../api/client";
import type { Batch, Movement } from "../api/types";
import DataGrid from "../components/ui/DataGrid";
import StatusBadge from "../components/ui/StatusBadge";
import { useIssueMaterial, useMovements, type IssuePayload } from "../hooks/useApi";

export default function IssuePage() {
  const { data: movements, isLoading } = useMovements();
  const issueMaterial = useIssueMaterial();

  const [scanId, setScanId] = useState("");
  const [lookupId, setLookupId] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const { data: batch, isFetching, error } = useQuery({
    queryKey: ["batch-lookup", lookupId],
    enabled: !!lookupId,
    queryFn: async () => (await api.get<Batch>(`/batches/${lookupId}`)).data,
    retry: false,
  });

  const { register, handleSubmit, reset } = useForm<{ department: string; requested_by: string; quantity: number; notes?: string }>();

  const onSubmit = handleSubmit(async (values) => {
    if (!batch) return;
    const payload: IssuePayload = {
      trace_id: batch.trace_id,
      department: values.department,
      requested_by: values.requested_by,
      quantity: Number(values.quantity),
      notes: values.notes,
    };
    const movement = await issueMaterial.mutateAsync(payload);
    setSuccessMsg(`Issued ${movement.quantity} ${batch.uom} under request ${movement.request_number}`);
    reset();
    setLookupId(null);
    setScanId("");
  });

  const columnDefs: ColDef<Movement>[] = [
    { field: "request_number", headerName: "Request #" },
    { field: "department", headerName: "Department" },
    { field: "requested_by", headerName: "Requested By" },
    { field: "quantity", headerName: "Qty", type: "numericColumn" },
    {
      field: "movement_date",
      headerName: "Date",
      valueFormatter: (p) => (p.value ? new Date(p.value).toLocaleString() : ""),
    },
  ];

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-xl font-bold text-industrial-900">Request &amp; Issue</h2>
        <p className="text-sm text-industrial-500">
          Scan a batch QR (or enter its Trace ID) to issue material against it.
        </p>
      </div>

      <div className="card p-5 space-y-4">
        <div className="flex gap-2">
          <input
            className="input max-w-sm"
            placeholder="Trace ID e.g. TRC-2026-000001"
            value={scanId}
            onChange={(e) => setScanId(e.target.value)}
          />
          <button className="btn-primary" onClick={() => setLookupId(scanId.trim())} disabled={!scanId.trim()}>
            {isFetching ? "Looking up..." : "Look Up Batch"}
          </button>
        </div>

        {error && <p className="text-sm text-red-500">Batch not found for that Trace ID.</p>}

        {batch && (
          <form onSubmit={onSubmit} className="space-y-4 pt-2 border-t border-industrial-100">
            <div className="flex items-center gap-3 flex-wrap">
              <span className="font-mono text-sm">{batch.trace_id}</span>
              <span className="text-sm text-industrial-600">{batch.product_name}</span>
              <StatusBadge status={batch.status} />
              <span className="text-sm text-industrial-500">
                Remaining: {batch.remaining_quantity} {batch.uom}
              </span>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="label">Department</label>
                <input className="input" {...register("department", { required: true })} />
              </div>
              <div>
                <label className="label">Requested By</label>
                <input className="input" {...register("requested_by", { required: true })} />
              </div>
              <div>
                <label className="label">Quantity to Issue</label>
                <input
                  type="number"
                  step="0.01"
                  max={batch.remaining_quantity}
                  className="input"
                  {...register("quantity", { required: true, min: 0.01, max: batch.remaining_quantity })}
                />
              </div>
              <div>
                <label className="label">Notes</label>
                <input className="input" {...register("notes")} />
              </div>
            </div>
            <div className="flex justify-end">
              <button type="submit" className="btn-accent" disabled={issueMaterial.isPending}>
                {issueMaterial.isPending ? "Issuing..." : "Issue Material"}
              </button>
            </div>
          </form>
        )}

        {successMsg && <p className="text-sm text-emerald-600">{successMsg}</p>}
      </div>

      <h3 className="text-sm font-semibold text-industrial-700">Recent Movements</h3>
      {isLoading ? (
        <div className="text-industrial-400 text-sm">Loading...</div>
      ) : (
        <div className="card p-2">
          <DataGrid rowData={movements ?? []} columnDefs={columnDefs} height={420} />
        </div>
      )}
    </div>
  );
}
