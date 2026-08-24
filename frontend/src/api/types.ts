export type ProductType = "RAW_MATERIAL" | "FINISHED_GOOD";
export type BatchType = "RAW_MATERIAL" | "FINISHED_GOOD";
export type BatchStatus = "ACTIVE" | "ISSUED_OUT" | "CONSUMED" | "DISPATCHED" | "EXPIRED";
export type BatchSourceType = "GRN" | "PRODUCTION";
export type MovementType =
  | "RECEIPT"
  | "ISSUE"
  | "PRODUCTION_CONSUMPTION"
  | "FINISHED_GOODS_CREATION"
  | "DISPATCH";
export type ProductionOrderStatus = "PLANNED" | "IN_PROGRESS" | "COMPLETED" | "CLOSED";
export type DispatchStatus = "PENDING" | "DISPATCHED" | "CANCELLED";
export type PackagingType =
  | "CAN"
  | "DRUM"
  | "BARREL"
  | "PAIL"
  | "BAG"
  | "BOX"
  | "TOTE"
  | "PALLET"
  | "OTHER";

export interface Supplier {
  id: number;
  code: string;
  name: string;
  contact_email?: string | null;
  contact_phone?: string | null;
  address?: string | null;
  erp_reference_no?: string | null;
}

export interface Customer {
  id: number;
  code: string;
  name: string;
  contact_email?: string | null;
  contact_phone?: string | null;
  address?: string | null;
  erp_reference_no?: string | null;
}

export interface Product {
  id: number;
  sku: string;
  name: string;
  category?: string | null;
  uom: string;
  product_type: ProductType;
  description?: string | null;
  erp_reference_no?: string | null;
}

export interface QRCode {
  id: number;
  trace_id: string;
  target_url: string;
  png_path: string;
  svg_path: string;
  print_count: number;
  download_count: number;
}

export interface Batch {
  id: number;
  batch_number: string;
  trace_id: string;
  product_id: number;
  batch_type: BatchType;
  source_type: BatchSourceType;
  status: BatchStatus;
  lot_number?: string | null;
  quantity: number;
  remaining_quantity: number;
  uom: string;
  manufacturing_date?: string | null;
  expiry_date?: string | null;
  warehouse_location?: string | null;
  packaging_type?: PackagingType | null;
  created_at: string;
  product_name?: string | null;
  product_sku?: string | null;
  qr_code?: QRCode | null;
}

export interface GRN {
  id: number;
  grn_number: string;
  supplier_id: number;
  product_id: number;
  batch_id: number;
  quantity: number;
  batch_number: string;
  lot_number?: string | null;
  manufacturing_date?: string | null;
  expiry_date?: string | null;
  warehouse_location: string;
  received_date: string;
  packaging_type?: PackagingType | null;
  supplier_name?: string | null;
  product_name?: string | null;
  trace_id?: string | null;
}

export interface Movement {
  id: number;
  movement_type: MovementType;
  batch_id: number;
  quantity: number;
  request_number?: string | null;
  department?: string | null;
  requested_by?: string | null;
  reference_type?: string | null;
  reference_id?: number | null;
  notes?: string | null;
  movement_date: string;
}

export interface ProductionOrder {
  id: number;
  production_order_no: string;
  product_id: number;
  planned_quantity: number;
  produced_quantity: number;
  status: ProductionOrderStatus;
  start_date?: string | null;
  end_date?: string | null;
  created_at: string;
  product_name?: string | null;
}

export interface ProductionConsumption {
  id: number;
  production_order_id: number;
  raw_batch_id: number;
  quantity_consumed: number;
  consumed_by?: string | null;
  consumed_at: string;
}

export interface FinishedGoods {
  id: number;
  fg_batch_number: string;
  batch_id: number;
  production_order_id: number;
  product_id: number;
  quantity: number;
  production_date: string;
  created_at: string;
  packaging_type?: PackagingType | null;
  product_name?: string | null;
  trace_id?: string | null;
}

export interface Dispatch {
  id: number;
  dispatch_number: string;
  customer_id: number;
  batch_id: number;
  quantity: number;
  dispatch_date: string;
  status: DispatchStatus;
  created_at: string;
  customer_name?: string | null;
  product_name?: string | null;
  trace_id?: string | null;
}

export interface AuditLog {
  id: number;
  action: string;
  entity_type: string;
  entity_id?: number | null;
  description: string;
  performed_by: string;
  created_at: string;
}

export interface DashboardSummary {
  total_grns: number;
  active_batches: number;
  production_orders: number;
  finished_goods_batches: number;
  dispatches: number;
  total_suppliers: number;
  total_products: number;
  total_customers: number;
}

export interface TrendPoint {
  label: string;
  value: number;
}

export interface DashboardTrends {
  batch_movement_trend: TrendPoint[];
  production_trend: TrendPoint[];
  dispatch_trend: TrendPoint[];
}

export interface TraceTimelineEvent {
  stage: string;
  title: string;
  timestamp: string;
  description: string;
  details: Record<string, unknown>;
}

export interface TraceabilityResponse {
  batch: {
    traceId: string;
    batchNumber: string;
    batchType: BatchType;
    status: BatchStatus;
    productId: number;
    productName: string;
    productSku: string;
    quantity: number;
    remainingQuantity: number;
    uom: string;
    warehouseLocation?: string | null;
    manufacturingDate?: string | null;
    expiryDate?: string | null;
    packagingType?: PackagingType | null;
    lotNumber?: string | null;
  };
  qrCode: { pngUrl: string; svgUrl: string; targetUrl: string } | null;
  timeline: TraceTimelineEvent[];
  upstreamRawMaterials: Array<Record<string, unknown>>;
  downstreamFinishedGoods: Array<Record<string, unknown>>;
}
