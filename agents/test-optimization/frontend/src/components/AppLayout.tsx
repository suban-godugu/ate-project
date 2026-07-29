import { NavLink, Outlet, useLocation } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  Activity,
  BarChart3,
  Gauge,
  ListChecks,
  Settings,
  Upload,
} from "lucide-react";
import { api } from "@/lib/api";

const NAV = [
  { to: "/", label: "Dashboard", icon: Gauge },
  { to: "/recommendations", label: "Recommendations", icon: ListChecks },
  { to: "/analytics", label: "Analytics", icon: BarChart3 },
  { to: "/upload", label: "Upload Dataset", icon: Upload },
  { to: "/settings", label: "Settings", icon: Settings },
];

/**
 * The dashboard embeds this app in an iframe with `?embed=1` to suppress duplicate chrome.
 * Detection also covers being framed, so in-app navigation that drops the query param
 * does not make the agent's own sidebar reappear inside the dashboard tab.
 */
export function useEmbedMode() {
  const { search } = useLocation();
  if (new URLSearchParams(search).get("embed") === "1") return true;
  try {
    return window.top !== window.self;
  } catch {
    // Cross-origin access to window.top throws, which itself means we are framed.
    return true;
  }
}

function EngineBadge() {
  const { data } = useQuery({
    queryKey: ["health"],
    queryFn: api.health,
    staleTime: 30_000,
  });

  if (!data) return null;

  const llm = data.llm_enabled;
  return (
    <div className="flex items-center gap-2">
      <span
        className={`inline-flex items-center gap-1.5 rounded-md border px-2 py-1 text-[11px] font-medium ${
          llm
            ? "border-brand-500/30 bg-brand-500/10 text-brand-300"
            : "border-emerald-500/30 bg-emerald-500/10 text-emerald-300"
        }`}
      >
        <Activity className="h-3 w-3" />
        {llm ? `LLM · ${data.model ?? "model"}` : "Heuristic engine"}
      </span>
      <span className="num text-[11px] text-ink-400">v{data.version}</span>
    </div>
  );
}

function Sidebar() {
  return (
    <aside className="hidden w-60 shrink-0 border-r border-white/8 bg-base-950/60 lg:block">
      <div className="flex h-14 items-center gap-2 border-b border-white/8 px-4">
        <div className="flex h-7 w-7 items-center justify-center rounded-md bg-brand-600 text-xs font-bold">
          TO
        </div>
        <div className="min-w-0">
          <p className="truncate text-xs font-semibold text-ink-100">Test Optimization</p>
          <p className="truncate text-[10px] text-ink-400">Recommendation Agent</p>
        </div>
      </div>
      <nav className="space-y-1 p-3">
        {NAV.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === "/"}
            className={({ isActive }) =>
              `flex items-center gap-2.5 rounded-lg px-3 py-2 text-xs font-medium transition ${
                isActive
                  ? "bg-brand-600/20 text-brand-300"
                  : "text-ink-300 hover:bg-white/5 hover:text-ink-100"
              }`
            }
          >
            <Icon className="h-4 w-4" />
            {label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}

export function AppLayout() {
  const embed = useEmbedMode();

  if (embed) {
    return (
      <div className="min-h-screen bg-base-900">
        <main className="px-4 py-5">
          <Outlet />
        </main>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen bg-base-900">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-14 items-center justify-between gap-4 border-b border-white/8 bg-base-950/60 px-5">
          <div className="min-w-0">
            <h1 className="truncate text-sm font-semibold text-ink-100">
              Test Optimization Recommendation Agent
            </h1>
            <p className="truncate text-[11px] text-ink-400">
              Final enterprise decision layer for ATE scan test strategy
            </p>
          </div>
          <EngineBadge />
        </header>
        <main className="flex-1 px-5 py-5">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
