import type { ColDef } from "ag-grid-community";
import { useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { useNavigate } from "react-router-dom";
import type { ProductionOrder } from "../api/types";
import DataGrid from "../components/ui/DataGrid";
import Modal from "../components/ui/Modal";
import StatusBadge from "../components/ui/StatusBadge";
import {
  useCreateProductionOrder,
  useProducts,
  useProductionOrders,
  type ProductionOrderCreatePayload,
} from "../hooks/useApi";

export default function ProductionPage() {
  const { data: orders, isLoading } = useProductionOrders();
  const { data: products } = useProducts();
  const createPO = useCreateProductionOrder();
  const navigate = useNavigate();
  const [showForm, setShowForm] = useState(false);

  const fgProducts = useMemo(
    () => (products ?? []).filter((p) => p.product_type === "FINISHED_GOOD"),
    [products]
  );

  const { register, handleSubmit, reset } = useForm<ProductionOrderCreatePayload>();

  const onSubmit = handleSubmit(async (values) => {
    await createPO.mutateAsync({
      ...values,
      product_id: Number(values.product_id),
      planned_quantity: Number(values.planned_quantity),
    });
    reset();
    setShowForm(false);
  });

  const columnDefs: ColDef<ProductionOrder>[] = [
    { field: "production_order_no", headerName: "PO #", pinned: "left" },
    { field: "product_name", headerName: "Product" },
    { field: "planned_quantity", headerName: "Planned", type: "numericColumn" },
    { field: "produced_quantity", headerName: "Produced", type: "numericColumn" },
    {
      field: "status",
      headerName: "Status",
      cellRenderer: (p: { value: string }) => <StatusBadge status={p.value} />,
    },
    { field: "start_date", headerName: "Start" },
    { field: "end_date", headerName: "End" },
  ];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-industrial-900">Production Orders</h2>
          <p className="text-sm text-industrial-500">
            Consume raw-material batches by QR scan, then generate finished-goods batches.
          </p>
        </div>
        <button className="btn-accent" onClick={() => setShowForm(true)}>
          + New Production Order
        </button>
      </div>

      {isLoading ? (
        <div className="text-industrial-400 text-sm">Loading...</div>
      ) : (
        <div className="card p-2">
          <DataGrid
            rowData={orders ?? []}
            columnDefs={columnDefs}
            onRowClicked={(row) => navigate(`/production/${row.id}`)}
          />
        </div>
      )}

      {showForm && (
        <Modal title="New Production Order" onClose={() => setShowForm(false)}>
          <form onSubmit={onSubmit} className="space-y-4">
            <div>
              <label className="label">Finished Good</label>
              <select className="input" {...register("product_id", { required: true })}>
                <option value="">Select product</option>
                {fgProducts.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.sku} &mdash; {p.name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="label">Planned Quantity</label>
              <input type="number" step="0.01" className="input" {...register("planned_quantity", { required: true, min: 0.01 })} />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="label">Start Date</label>
                <input type="date" className="input" {...register("start_date")} />
              </div>
              <div>
                <label className="label">End Date</label>
                <input type="date" className="input" {...register("end_date")} />
              </div>
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <button type="button" className="btn-secondary" onClick={() => setShowForm(false)}>
                Cancel
              </button>
              <button type="submit" className="btn-accent" disabled={createPO.isPending}>
                Create
              </button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}
