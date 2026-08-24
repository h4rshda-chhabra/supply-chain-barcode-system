import { NavLink } from "react-router-dom";

const navItems = [
  { to: "/", label: "Dashboard", icon: "▦" },
  { to: "/grn", label: "Goods Receipt", icon: "▼" },
  { to: "/batches", label: "Batches", icon: "▣" },
  { to: "/issue", label: "Request & Issue", icon: "⇄" },
  { to: "/production", label: "Production", icon: "⚙" },
  { to: "/finished-goods", label: "Finished Goods", icon: "◆" },
  { to: "/dispatch", label: "Dispatch", icon: "▲" },
  { to: "/reports", label: "Reports", icon: "≡" },
];

export default function Sidebar() {
  return (
    <aside className="w-60 shrink-0 bg-industrial-900 text-industrial-100 min-h-screen flex flex-col">
      <div className="px-5 py-5 border-b border-industrial-800">
        <div className="text-lg font-bold tracking-tight text-white">TraceChain</div>
        <div className="text-[11px] text-industrial-400 uppercase tracking-wider">
          QR Traceability Platform
        </div>
      </div>
      <nav className="flex-1 py-3">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === "/"}
            className={({ isActive }) =>
              `flex items-center gap-3 px-5 py-2.5 text-sm font-medium border-l-2 transition-colors ${
                isActive
                  ? "border-accent-500 bg-industrial-800 text-white"
                  : "border-transparent text-industrial-300 hover:bg-industrial-800 hover:text-white"
              }`
            }
          >
            <span className="w-4 text-center text-industrial-400">{item.icon}</span>
            {item.label}
          </NavLink>
        ))}
      </nav>
      <div className="px-5 py-4 text-[11px] text-industrial-500 border-t border-industrial-800">
        MVP build &middot; No auth &middot; PostgreSQL
      </div>
    </aside>
  );
}
