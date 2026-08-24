import type { ColDef } from "ag-grid-community";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { useForm } from "react-hook-form";
import api from "../api/client";
import type { Batch, Dispatch } from "../api/types";
import DataGrid from "../components/ui/DataGrid";
import StatusBadge from "../components/ui/StatusBadge";
import { useCreateDispatch, useCustomers, useDispatches, type DispatchCreatePayload } from "../hooks/useApi";

export default function DispatchPage() {
  const { data: dispatches, isLoading } = useDispatches();
  const { data: customers } = useCustomers();
  const createDispatch = useCreateDispatch();

  const [scanId, setScanId] = useState("");
  const [lookupId, setLookupId] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);

  const { data: batch, isFetching, error } = useQuery({
    queryKey: ["dispatch-batch-lookup", lookupId],
    enabled: !!lookupId,
    queryFn: async () => (await api.get<Batch>(`/batches/${lookupId}`)).data,
    retry: false,
  });

  const { register, handleSubmit, reset } = useForm<{ customer_id: string; quantity: number; dispatch_date: string }>();

  const onSubmit = handleSubmit(async (values) => {
    if (!batch) return;
    setFormError(null);
    const payload: DispatchCreatePayload = {
      customer_id: Number(values.customer_id),
      trace_id: batch.trace_id,
      quantity: Number(values.quantity),
      dispatch_date: values.dispatch_date,
    };
    try {
      const dispatch = await createDispatch.mutateAsync(payload);
      setSuccessMsg(`Dispatch ${dispatch.dispatch_number} created for ${dispatch.quantity} ${batch.uom}`);
      reset();
      setLookupId(null);
      setScanId("");
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      setFormError(err.response?.data?.detail ?? "Failed to create dispatch");
    }
  });

  const columnDefs: ColDef<Dispatch>[] = [
    { field: "dispatch_number", headerName: "Dispatch #", pinned: "left" },
    { field: "trace_id", headerName: "Trace ID" },
    { field: "customer_name", headerName: "Customer" },
    { field: "product_name", headerName: "Product" },
    { field: "quantity", headerName: "Qty", type: "numericColumn" },
    {
      field: "status",
      headerName: "Status",
      cellRenderer: (p: { value: string }) => <StatusBadge status={p.value} />,
    },
    { field: "dispatch_date", headerName: "Dispatch Date" },
  ];

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-xl font-bold text-industrial-900">Dispatch</h2>
        <p className="text-sm text-industrial-500">
          Scan a finished-goods QR before dispatch to a customer.
        </p>
      </div>

      <div className="card p-5 space-y-4">
        <div className="flex gap-2">
          <input
            className="input max-w-sm"
            placeholder="Trace ID e.g. TRC-2026-000123"
            value={scanId}
            onChange={(e) => setScanId(e.target.value)}
          />
          <button className="btn-primary" onClick={() => setLookupId(scanId.trim())} disabled={!scanId.trim()}>
            {isFetching ? "Looking up..." : "Look Up Batch"}
          </button>
        </div>

        {error && <p className="text-sm text-red-500">Batch not found for that Trace ID.</p>}
        {batch && batch.batch_type !== "FINISHED_GOOD" && (
          <p className="text-sm text-amber-600">This is a raw-material batch, not a finished good.</p>
        )}

        {batch && batch.batch_type === "FINISHED_GOOD" && (
          <form onSubmit={onSubmit} className="space-y-4 pt-2 border-t border-industrial-100">
            <div className="flex items-center gap-3 flex-wrap">
              <span className="font-mono text-sm">{batch.trace_id}</span>
              <span className="text-sm text-industrial-600">{batch.product_name}</span>
              <StatusBadge status={batch.status} />
              <span className="text-sm text-industrial-500">
                Remaining: {batch.remaining_quantity} {batch.uom}
              </span>
            </div>
            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="label">Customer</label>
                <select className="input" {...register("customer_id", { required: true })}>
                  <option value="">Select customer</option>
                  {customers?.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.code} &mdash; {c.name}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="label">Quantity</label>
                <input
                  type="number"
                  step="0.01"
                  max={batch.remaining_quantity}
                  className="input"
                  {...register("quantity", { required: true, min: 0.01, max: batch.remaining_quantity })}
                />
              </div>
              <div>
                <label className="label">Dispatch Date</label>
                <input type="date" className="input" {...register("dispatch_date", { required: true })} />
              </div>
            </div>
            {formError && <p className="text-xs text-red-500">{formError}</p>}
            <div className="flex justify-end">
              <button type="submit" className="btn-accent" disabled={createDispatch.isPending}>
                {createDispatch.isPending ? "Dispatching..." : "Confirm Dispatch"}
              </button>
            </div>
          </form>
        )}

        {successMsg && <p className="text-sm text-emerald-600">{successMsg}</p>}
      </div>

      <h3 className="text-sm font-semibold text-industrial-700">Dispatch History</h3>
      {isLoading ? (
        <div className="text-industrial-400 text-sm">Loading...</div>
      ) : (
        <div className="card p-2">
          <DataGrid rowData={dispatches ?? []} columnDefs={columnDefs} height={420} />
        </div>
      )}
    </div>
  );
}
