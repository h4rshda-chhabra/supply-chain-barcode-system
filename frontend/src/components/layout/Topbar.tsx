import { useState } from "react";
import { useNavigate } from "react-router-dom";

export default function Topbar() {
  const [traceId, setTraceId] = useState("");
  const navigate = useNavigate();

  const onScanSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (traceId.trim()) {
      navigate(`/trace/${traceId.trim()}`);
      setTraceId("");
    }
  };

  return (
    <header className="h-16 bg-white border-b border-industrial-200 flex items-center justify-between px-6 sticky top-0 z-10">
      <div>
        <h1 className="text-sm font-semibold text-industrial-800">
          Manufacturing Traceability Console
        </h1>
      </div>
      <form onSubmit={onScanSubmit} className="flex items-center gap-2">
        <input
          value={traceId}
          onChange={(e) => setTraceId(e.target.value)}
          placeholder="Scan or enter Trace ID (e.g. TRC-2026-000001)"
          className="input w-80"
        />
        <button type="submit" className="btn-primary">
          Trace
        </button>
      </form>
    </header>
  );
}
