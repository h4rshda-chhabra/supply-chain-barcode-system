import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { Link, useNavigate, useParams } from "react-router-dom";
import api from "../api/client";
import type { ProductionOrder } from "../api/types";
import QRPreview from "../components/QRPreview";
import Modal from "../components/ui/Modal";
import StatusBadge from "../components/ui/StatusBadge";
import {
  useConsumeBatch,
  useCreateFinishedGoods,
  useProductionOrderConsumption,
  type ConsumePayload,
  type FGCreatePayload,
} from "../hooks/useApi";

export default function ProductionDetailPage() {
  const { id } = useParams<{ id: string }>();
  const poId = Number(id);
  const navigate = useNavigate();

  const { data: po, isLoading } = useQuery({
    queryKey: ["production-order", poId],
    queryFn: async () => (await api.get<ProductionOrder>(`/production-orders/${poId}`)).data,
  });
  const { data: consumption } = useProductionOrderConsumption(poId);
  const consumeBatch = useConsumeBatch(poId);
  const createFG = useCreateFinishedGoods();

  const [createdTraceId, setCreatedTraceId] = useState<string | null>(null);
  const [consumeError, setConsumeError] = useState<string | null>(null);
  const [showFGForm, setShowFGForm] = useState(false);

  const consumeForm = useForm<ConsumePayload>();
  const fgForm = useForm<{
    quantity: number;
    production_date: string;
    warehouse_location?: string;
    packaging_type?: string;
  }>();

  const onConsume = consumeForm.handleSubmit(async (values) => {
    setConsumeError(null);
    try {
      await consumeBatch.mutateAsync({
        trace_id: values.trace_id,
        quantity_consumed: Number(values.quantity_consumed),
        consumed_by: values.consumed_by,
      });
      consumeForm.reset();
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      setConsumeError(err.response?.data?.detail ?? "Failed to record consumption");
    }
  });

  const onCreateFG = fgForm.handleSubmit(async (values) => {
    if (!po) return;
    const payload: FGCreatePayload = {
      production_order_id: po.id,
      quantity: Number(values.quantity),
      production_date: values.production_date,
      warehouse_location: values.warehouse_location,
      packaging_type: (values.packaging_type || undefined) as FGCreatePayload["packaging_type"],
    };
    const fg = await createFG.mutateAsync(payload);
    setShowFGForm(false);
    setCreatedTraceId(fg.trace_id ?? null);
    fgForm.reset();
  });

  if (isLoading || !po) {
    return <div className="text-industrial-400 text-sm">Loading production order...</div>;
  }

  return (
    <div className="space-y-6">
      <button className="text-sm text-industrial-500 hover:text-industrial-800" onClick={() => navigate(-1)}>
        &larr; Back to Production Orders
      </button>

      <div className="card p-5 flex flex-wrap items-center gap-4 justify-between">
        <div>
          <h2 className="text-xl font-bold text-industrial-900">{po.production_order_no}</h2>
          <p className="text-sm text-industrial-500">{po.product_name}</p>
        </div>
        <div className="flex items-center gap-4">
          <StatusBadge status={po.status} />
          <div className="text-sm text-industrial-600">
            {po.produced_quantity} / {po.planned_quantity} produced
          </div>
          <button className="btn-accent" onClick={() => setShowFGForm(true)}>
            + Create Finished Goods Batch
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card p-5 space-y-4">
          <h3 className="font-semibold text-industrial-800">Scan Raw Material for Consumption</h3>
          <form onSubmit={onConsume} className="space-y-3">
            <div>
              <label className="label">Trace ID (scan QR)</label>
              <input className="input" placeholder="TRC-2026-000001" {...consumeForm.register("trace_id", { required: true })} />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="label">Quantity Consumed</label>
                <input type="number" step="0.01" className="input" {...consumeForm.register("quantity_consumed", { required: true, min: 0.01 })} />
              </div>
              <div>
                <label className="label">Consumed By</label>
                <input className="input" {...consumeForm.register("consumed_by")} />
              </div>
            </div>
            {consumeError && <p className="text-xs text-red-500">{consumeError}</p>}
            <button type="submit" className="btn-primary w-full" disabled={consumeBatch.isPending}>
              {consumeBatch.isPending ? "Recording..." : "Record Consumption"}
            </button>
          </form>
        </div>

        <div className="card p-5">
          <h3 className="font-semibold text-industrial-800 mb-3">Raw Materials Consumed</h3>
          {!consumption || consumption.length === 0 ? (
            <p className="text-sm text-industrial-400">No consumption recorded yet.</p>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-industrial-500 text-xs uppercase border-b border-industrial-100">
                  <th className="py-2">Batch ID</th>
                  <th>Qty</th>
                  <th>By</th>
                  <th>When</th>
                </tr>
              </thead>
              <tbody>
                {consumption.map((c) => (
                  <tr key={c.id} className="border-b border-industrial-50">
                    <td className="py-2">#{c.raw_batch_id}</td>
                    <td>{c.quantity_consumed}</td>
                    <td>{c.consumed_by ?? "-"}</td>
                    <td>{new Date(c.consumed_at).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {showFGForm && (
        <Modal title="Create Finished Goods Batch" onClose={() => setShowFGForm(false)}>
          <form onSubmit={onCreateFG} className="space-y-4">
            <div>
              <label className="label">Quantity</label>
              <input type="number" step="0.01" className="input" {...fgForm.register("quantity", { required: true, min: 0.01 })} />
            </div>
            <div>
              <label className="label">Production Date</label>
              <input type="date" className="input" {...fgForm.register("production_date", { required: true })} />
            </div>
            <div>
              <label className="label">Warehouse Location</label>
              <input className="input" {...fgForm.register("warehouse_location")} />
            </div>
            <div>
              <label className="label">Packaging Type</label>
              <select className="input" {...fgForm.register("packaging_type")}>
                <option value="">Select packaging</option>
                <option value="DRUM">Drum</option>
                <option value="BARREL">Barrel</option>
                <option value="CAN">Can</option>
                <option value="PAIL">Pail</option>
                <option value="BAG">Bag</option>
                <option value="BOX">Box</option>
                <option value="TOTE">Tote</option>
                <option value="PALLET">Pallet</option>
                <option value="OTHER">Other</option>
              </select>
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <button type="button" className="btn-secondary" onClick={() => setShowFGForm(false)}>
                Cancel
              </button>
              <button type="submit" className="btn-accent" disabled={createFG.isPending}>
                Create &amp; Generate QR
              </button>
            </div>
          </form>
        </Modal>
      )}

      {createdTraceId && (
        <Modal title="Finished Goods Batch Created" onClose={() => setCreatedTraceId(null)}>
          <div className="text-center space-y-3">
            <p className="text-sm text-industrial-600">
              Trace ID <span className="font-mono font-semibold">{createdTraceId}</span>
            </p>
            <QRPreview traceId={createdTraceId} />
            <Link to={`/trace/${createdTraceId}`} className="btn-primary inline-flex" onClick={() => setCreatedTraceId(null)}>
              View Traceability
            </Link>
          </div>
        </Modal>
      )}
    </div>
  );
}
