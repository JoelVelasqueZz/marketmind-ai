import { NavLink } from "react-router-dom";

const NAV_ITEMS = [
  { to: "/", label: "Dashboard", icon: "dashboard" },
  { to: "/radar", label: "News Radar", icon: "analytics" },
  { to: "/analysis", label: "AI Analysis", icon: "psychology" },
  { to: "/briefings", label: "Briefings", icon: "description" },
  { to: "/watchlist", label: "Watchlist", icon: "visibility" },
];

export default function Sidebar() {
  return (
    <aside className="w-[280px] h-screen fixed left-0 top-0 overflow-y-auto border-r border-outline-variant bg-surface-container shadow-sm flex flex-col p-gutter z-50">
      <div className="mb-stack-lg">
        <h1 className="font-headline-lg text-headline-lg font-bold text-primary tracking-tight">
          MarketMind AI
        </h1>
        <p className="font-label-md text-label-md text-on-surface-variant opacity-70">
          Financial Intelligence · Track 5
        </p>
      </div>
      <nav className="flex-1 space-y-1">
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === "/"}
            className={({ isActive }) =>
              [
                "flex items-center gap-3 px-4 py-3 rounded-lg transition-colors duration-200 group",
                isActive
                  ? "text-on-primary-fixed bg-primary-container font-bold border-l-4 border-primary"
                  : "text-on-surface-variant hover:text-on-surface hover:bg-surface-variant",
              ].join(" ")
            }
          >
            <span className="material-symbols-outlined group-hover:scale-110 transition-transform">
              {item.icon}
            </span>
            <span className="font-label-md text-label-md">{item.label}</span>
          </NavLink>
        ))}
      </nav>
      <div className="mt-auto border-t border-outline-variant pt-stack-md">
        <div className="flex items-center gap-3 px-2">
          <div className="w-10 h-10 rounded-full border border-outline-variant bg-surface-variant flex items-center justify-center">
            <span className="material-symbols-outlined text-on-surface-variant">person</span>
          </div>
          <div>
            <p className="font-label-md text-label-md font-bold text-on-surface">Equipo Track 5</p>
            <p className="text-[10px] text-on-surface-variant">Modo demo · datos mock</p>
          </div>
        </div>
      </div>
    </aside>
  );
}
