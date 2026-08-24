import { Route, Routes } from "react-router-dom";
import Layout from "./components/layout/Layout";
import BatchesPage from "./pages/Batches";
import DashboardPage from "./pages/Dashboard";
import DispatchPage from "./pages/Dispatch";
import FinishedGoodsPage from "./pages/FinishedGoods";
import GRNPage from "./pages/GRN";
import IssuePage from "./pages/Issue";
import ProductionDetailPage from "./pages/ProductionDetail";
import ProductionPage from "./pages/Production";
import ReportsPage from "./pages/Reports";
import TraceabilityPage from "./pages/Traceability";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/grn" element={<GRNPage />} />
        <Route path="/batches" element={<BatchesPage />} />
        <Route path="/issue" element={<IssuePage />} />
        <Route path="/production" element={<ProductionPage />} />
        <Route path="/production/:id" element={<ProductionDetailPage />} />
        <Route path="/finished-goods" element={<FinishedGoodsPage />} />
        <Route path="/dispatch" element={<DispatchPage />} />
        <Route path="/reports" element={<ReportsPage />} />
        <Route path="/trace/:traceId" element={<TraceabilityPage />} />
        <Route path="*" element={<div className="text-industrial-500">Page not found.</div>} />
      </Route>
    </Routes>
  );
}
