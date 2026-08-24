import { AgGridReact } from "ag-grid-react";
import "ag-grid-community/styles/ag-grid.css";
import "ag-grid-community/styles/ag-theme-quartz.css";
import type { ColDef } from "ag-grid-community";

interface DataGridProps<T> {
  rowData: T[];
  columnDefs: ColDef<T>[];
  height?: number;
  onRowClicked?: (row: T) => void;
}

export default function DataGrid<T>({ rowData, columnDefs, height = 520, onRowClicked }: DataGridProps<T>) {
  return (
    <div className="ag-theme-quartz" style={{ height, width: "100%" }}>
      <AgGridReact<T>
        rowData={rowData}
        columnDefs={columnDefs}
        defaultColDef={{ sortable: true, filter: true, resizable: true, flex: 1, minWidth: 120 }}
        pagination
        paginationPageSize={20}
        paginationPageSizeSelector={[10, 20, 50, 100]}
        onRowClicked={onRowClicked ? (e) => onRowClicked(e.data as T) : undefined}
        rowSelection={onRowClicked ? "single" : undefined}
        animateRows
      />
    </div>
  );
}
