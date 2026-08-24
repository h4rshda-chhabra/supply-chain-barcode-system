import { useQuery } from "@tanstack/react-query";
import api from "../api/client";
import type { QRCode } from "../api/types";
import { useReprintQR } from "../hooks/useApi";

export default function QRPreview({ traceId }: { traceId: string }) {
  const { data: qr, isLoading } = useQuery({
    queryKey: ["qr", traceId],
    queryFn: async () => (await api.get<QRCode>(`/qr-codes/${traceId}`)).data,
  });
  const reprint = useReprintQR();

  if (isLoading || !qr) {
    return <div className="text-sm text-industrial-400">Loading QR code...</div>;
  }

  return (
    <div className="flex flex-col items-center gap-3">
      <img
        src={qr.png_path}
        alt={`QR code for ${traceId}`}
        className="w-40 h-40 border border-industrial-200 rounded-md p-2 bg-white"
      />
      <div className="flex flex-wrap justify-center gap-2">
        <a className="btn-secondary" href={`/api/v1/qr-codes/${traceId}/download?format=png`} download>
          Download PNG
        </a>
        <a className="btn-secondary" href={`/api/v1/qr-codes/${traceId}/download?format=svg`} download>
          Download SVG
        </a>
        <button
          className="btn-secondary"
          onClick={() => {
            reprint.mutate(traceId);
            window.open(qr.png_path, "_blank");
          }}
        >
          Reprint
        </button>
      </div>
      <p className="text-[11px] text-industrial-400">
        Printed {qr.print_count}x &middot; Downloaded {qr.download_count}x
      </p>
    </div>
  );
}
