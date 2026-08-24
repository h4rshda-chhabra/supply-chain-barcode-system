import type { ColDef } from "ag-grid-community";
import { useNavigate } from "react-router-dom";
import type { FinishedGoods } from "../api/types";
import DataGrid from "../components/ui/DataGrid";
import { useFinishedGoods } from "../hooks/useApi";

export default function FinishedGoodsPage() {
  const { data: items, isLoading } = useFinishedGoods();
  const navigate = useNavigate();

  const columnDefs: ColDef<FinishedGoods>[] = [
    { field: "fg_batch_number", headerName: "FG Batch #", pinned: "left" },
    { field: "trace_id", headerName: "Trace ID" },
    { field: "product_name", headerName: "Product" },
    { field: "quantity", headerName: "Qty", type: "numericColumn" },
    { field: "packaging_type", headerName: "Packaging" },
    { field: "production_date", headerName: "Production Date" },
    {
      field: "created_at",
      headerName: "Created",
      valueFormatter: (p) => (p.value ? new Date(p.value).toLocaleString() : ""),
    },
  ];

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-xl font-bold text-industrial-900">Finished Goods</h2>
        <p className="text-sm text-industrial-500">
          Finished-goods batches produced from production orders. Each carries its own Trace ID and QR code.
        </p>
      </div>

      {isLoading ? (
        <div className="text-industrial-400 text-sm">Loading...</div>
      ) : (
        <div className="card p-2">
          <DataGrid
            rowData={items ?? []}
            columnDefs={columnDefs}
            onRowClicked={(row) => row.trace_id && navigate(`/trace/${row.trace_id}`)}
          />
        </div>
      )}
    </div>
  );
}
