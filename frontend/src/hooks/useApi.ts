import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import api from "../api/client";
import type {
  AuditLog,
  Batch,
  Customer,
  DashboardSummary,
  DashboardTrends,
  Dispatch,
  FinishedGoods,
  GRN,
  Movement,
  PackagingType,
  Product,
  ProductionConsumption,
  ProductionOrder,
  Supplier,
  TraceabilityResponse,
} from "../api/types";

// ---------- Master data ----------
export const useSuppliers = () =>
  useQuery({ queryKey: ["suppliers"], queryFn: async () => (await api.get<Supplier[]>("/suppliers")).data });

export const useCustomers = () =>
  useQuery({ queryKey: ["customers"], queryFn: async () => (await api.get<Customer[]>("/customers")).data });

export const useProducts = () =>
  useQuery({ queryKey: ["products"], queryFn: async () => (await api.get<Product[]>("/products")).data });

// ---------- GRN ----------
export const useGRNs = () =>
  useQuery({ queryKey: ["grns"], queryFn: async () => (await api.get<GRN[]>("/grns")).data });

export interface GRNCreatePayload {
  supplier_id: number;
  product_id: number;
  quantity: number;
  batch_number: string;
  lot_number?: string;
  manufacturing_date?: string;
  expiry_date?: string;
  warehouse_location: string;
  uom?: string;
  packaging_type?: PackagingType;
}

export const useCreateGRN = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: GRNCreatePayload) => (await api.post<GRN>("/grns", payload)).data,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["grns"] });
      qc.invalidateQueries({ queryKey: ["batches"] });
      qc.invalidateQueries({ queryKey: ["dashboard-summary"] });
    },
  });
};

// ---------- Batches ----------
export const useBatches = (params?: { search?: string; batch_type?: string; status?: string }) =>
  useQuery({
    queryKey: ["batches", params],
    queryFn: async () => (await api.get<Batch[]>("/batches", { params })).data,
  });

// ---------- Request & Issue ----------
export const useMovements = () =>
  useQuery({ queryKey: ["movements"], queryFn: async () => (await api.get<Movement[]>("/movements")).data });

export interface IssuePayload {
  trace_id: string;
  department: string;
  requested_by: string;
  quantity: number;
  notes?: string;
}

export const useIssueMaterial = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: IssuePayload) => (await api.post<Movement>("/movements/issue", payload)).data,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["movements"] });
      qc.invalidateQueries({ queryKey: ["batches"] });
    },
  });
};

// ---------- Production ----------
export const useProductionOrders = () =>
  useQuery({
    queryKey: ["production-orders"],
    queryFn: async () => (await api.get<ProductionOrder[]>("/production-orders")).data,
  });

export interface ProductionOrderCreatePayload {
  product_id: number;
  planned_quantity: number;
  start_date?: string;
  end_date?: string;
}

export const useCreateProductionOrder = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: ProductionOrderCreatePayload) =>
      (await api.post<ProductionOrder>("/production-orders", payload)).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["production-orders"] }),
  });
};

export const useProductionOrderConsumption = (poId: number | undefined) =>
  useQuery({
    queryKey: ["production-consumption", poId],
    enabled: !!poId,
    queryFn: async () =>
      (await api.get<ProductionConsumption[]>(`/production-orders/${poId}/consumption`)).data,
  });

export interface ConsumePayload {
  trace_id: string;
  quantity_consumed: number;
  consumed_by?: string;
}

export const useConsumeBatch = (poId: number | undefined) => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: ConsumePayload) =>
      (await api.post(`/production-orders/${poId}/consume`, payload)).data,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["production-consumption", poId] });
      qc.invalidateQueries({ queryKey: ["production-orders"] });
      qc.invalidateQueries({ queryKey: ["batches"] });
    },
  });
};

// ---------- Finished Goods ----------
export const useFinishedGoods = () =>
  useQuery({
    queryKey: ["finished-goods"],
    queryFn: async () => (await api.get<FinishedGoods[]>("/finished-goods")).data,
  });

export interface FGCreatePayload {
  production_order_id: number;
  quantity: number;
  production_date: string;
  warehouse_location?: string;
  packaging_type?: PackagingType;
}

export const useCreateFinishedGoods = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: FGCreatePayload) =>
      (await api.post<FinishedGoods>("/finished-goods", payload)).data,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["finished-goods"] });
      qc.invalidateQueries({ queryKey: ["production-orders"] });
      qc.invalidateQueries({ queryKey: ["batches"] });
    },
  });
};

// ---------- Dispatch ----------
export const useDispatches = () =>
  useQuery({ queryKey: ["dispatches"], queryFn: async () => (await api.get<Dispatch[]>("/dispatches")).data });

export interface DispatchCreatePayload {
  customer_id: number;
  trace_id: string;
  quantity: number;
  dispatch_date: string;
}

export const useCreateDispatch = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: DispatchCreatePayload) =>
      (await api.post<Dispatch>("/dispatches", payload)).data,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["dispatches"] });
      qc.invalidateQueries({ queryKey: ["batches"] });
    },
  });
};

// ---------- Traceability ----------
export const useTraceability = (traceId: string | undefined) =>
  useQuery({
    queryKey: ["trace", traceId],
    enabled: !!traceId,
    queryFn: async () => (await api.get<TraceabilityResponse>(`/trace/${traceId}`)).data,
  });

// ---------- Dashboard ----------
export const useDashboardSummary = () =>
  useQuery({
    queryKey: ["dashboard-summary"],
    queryFn: async () => (await api.get<DashboardSummary>("/dashboard/summary")).data,
  });

export const useDashboardTrends = () =>
  useQuery({
    queryKey: ["dashboard-trends"],
    queryFn: async () => (await api.get<DashboardTrends>("/dashboard/trends")).data,
  });

// ---------- Audit ----------
export const useAuditLogs = () =>
  useQuery({ queryKey: ["audit-logs"], queryFn: async () => (await api.get<AuditLog[]>("/audit-logs")).data });

// ---------- QR ----------
export const useReprintQR = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (traceId: string) => (await api.post(`/qr-codes/${traceId}/print`)).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["trace"] }),
  });
};
