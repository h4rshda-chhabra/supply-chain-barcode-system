import type { ColDef } from "ag-grid-community";
import { useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { Link } from "react-router-dom";
import DataGrid from "../components/ui/DataGrid";
import Modal from "../components/ui/Modal";
import QRPreview from "../components/QRPreview";
import { useCreateGRN, useGRNs, useProducts, useSuppliers, type GRNCreatePayload } from "../hooks/useApi";
import type { GRN } from "../api/types";

export default function GRNPage() {
  const { data: grns, isLoading } = useGRNs();
  const { data: suppliers } = useSuppliers();
  const { data: products } = useProducts();
  const createGRN = useCreateGRN();

  const [showForm, setShowForm] = useState(false);
  const [createdTraceId, setCreatedTraceId] = useState<string | null>(null);

  const rawProducts = useMemo(
    () => (products ?? []).filter((p) => p.product_type === "RAW_MATERIAL"),
    [products]
  );

  const { register, handleSubmit, reset, formState: { errors } } = useForm<GRNCreatePayload>({
    defaultValues: { uom: "EA" },
  });

  const onSubmit = handleSubmit(async (values) => {
    const payload: GRNCreatePayload = {
      ...values,
      supplier_id: Number(values.supplier_id),
      product_id: Number(values.product_id),
      quantity: Number(values.quantity),
      packaging_type: values.packaging_type || undefined,
    };
    const grn = await createGRN.mutateAsync(payload);
    setCreatedTraceId(grn.trace_id ?? null);
    reset();
  });

  const columnDefs: ColDef<GRN>[] = [
    { field: "grn_number", headerName: "GRN #", pinned: "left" },
    { field: "trace_id", headerName: "Trace ID" },
    { field: "supplier_name", headerName: "Supplier" },
    { field: "product_name", headerName: "Product" },
    { field: "batch_number", headerName: "Batch #" },
    { field: "lot_number", headerName: "Lot #" },
    { field: "packaging_type", headerName: "Packaging" },
    { field: "quantity", headerName: "Qty", type: "numericColumn" },
    { field: "warehouse_location", headerName: "Warehouse" },
    {
      field: "received_date",
      headerName: "Received",
      valueFormatter: (p) => (p.value ? new Date(p.value).toLocaleString() : ""),
    },
  ];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-industrial-900">Goods Receipt (GRN)</h2>
          <p className="text-sm text-industrial-500">
            Receive raw materials from suppliers &mdash; generates a Trace ID and QR code per batch.
          </p>
        </div>
        <button className="btn-accent" onClick={() => setShowForm(true)}>
          + New GRN
        </button>
      </div>

      {isLoading ? (
        <div className="text-industrial-400 text-sm">Loading...</div>
      ) : (
        <div className="card p-2">
          <DataGrid rowData={grns ?? []} columnDefs={columnDefs} />
        </div>
      )}

      {showForm && (
        <Modal title="New Goods Receipt Note" onClose={() => setShowForm(false)} wide>
          <form onSubmit={onSubmit} className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">Supplier</label>
              <select className="input" {...register("supplier_id", { required: true })}>
                <option value="">Select supplier</option>
                {suppliers?.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.code} &mdash; {s.name}
                  </option>
                ))}
              </select>
              {errors.supplier_id && <p className="text-xs text-red-500 mt-1">Required</p>}
            </div>
            <div>
              <label className="label">Product</label>
              <select className="input" {...register("product_id", { required: true })}>
                <option value="">Select product</option>
                {rawProducts.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.sku} &mdash; {p.name}
                  </option>
                ))}
              </select>
              {errors.product_id && <p className="text-xs text-red-500 mt-1">Required</p>}
            </div>
            <div>
              <label className="label">Quantity</label>
              <input type="number" step="0.01" className="input" {...register("quantity", { required: true, min: 0.01 })} />
            </div>
            <div>
              <label className="label">UoM</label>
              <input className="input" {...register("uom")} />
            </div>
            <div>
              <label className="label">Packaging Type</label>
              <select className="input" {...register("packaging_type")}>
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
            <div>
              <label className="label">Batch Number</label>
              <input className="input" {...register("batch_number", { required: true })} />
            </div>
            <div>
              <label className="label">Lot Number</label>
              <input className="input" {...register("lot_number")} />
            </div>
            <div>
              <label className="label">Manufacturing Date</label>
              <input type="date" className="input" {...register("manufacturing_date")} />
            </div>
            <div>
              <label className="label">Expiry Date</label>
              <input type="date" className="input" {...register("expiry_date")} />
            </div>
            <div className="col-span-2">
              <label className="label">Warehouse Location</label>
              <input className="input" {...register("warehouse_location", { required: true })} />
            </div>
            <div className="col-span-2 flex justify-end gap-2 pt-2">
              <button type="button" className="btn-secondary" onClick={() => setShowForm(false)}>
                Cancel
              </button>
              <button type="submit" className="btn-accent" disabled={createGRN.isPending}>
                {createGRN.isPending ? "Creating..." : "Create GRN & Generate QR"}
              </button>
            </div>
          </form>
        </Modal>
      )}

      {createdTraceId && (
        <Modal title="GRN Created" onClose={() => setCreatedTraceId(null)}>
          <div className="text-center space-y-3">
            <p className="text-sm text-industrial-600">
              Batch created with Trace ID <span className="font-mono font-semibold">{createdTraceId}</span>
            </p>
            <QRPreview traceId={createdTraceId} />
            <Link
              to={`/trace/${createdTraceId}`}
              className="btn-primary inline-flex"
              onClick={() => setCreatedTraceId(null)}
            >
              View Traceability
            </Link>
          </div>
        </Modal>
      )}
    </div>
  );
}
