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

function withEmbedParam(to: string, embed: boolean): string {
  if (!embed) return to;
  const [path, qs = ""] = to.split("?");
  const params = new URLSearchParams(qs);
  params.set("embed", "1");
  return `${path}?${params.toString()}`;
}

/** True when hosted inside the VERILUMEN dashboard iframe. */
export function useEmbedMode() {
  const { search } = useLocation();
  return new URLSearchParams(search).get("embed") === "1";
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

function Sidebar({ embed }: { embed: boolean }) {
  return (
    <aside className="flex w-52 shrink-0 flex-col border-r border-white/8 bg-base-950/60">
      <div className="flex h-12 items-center gap-2 border-b border-white/8 px-3">
        <div className="flex h-7 w-7 items-center justify-center rounded-md bg-brand-600 text-xs font-bold">
          TO
        </div>
        <div className="min-w-0">
          <p className="truncate text-xs font-semibold text-ink-100">Test Optimization</p>
          <p className="truncate text-[10px] text-ink-400">Recommendation Agent</p>
        </div>
      </div>
      <nav className="space-y-0.5 p-2">
        {NAV.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={withEmbedParam(to, embed)}
            end={to === "/"}
            className={({ isActive }) =>
              `flex items-center gap-2 rounded-lg px-2.5 py-1.5 text-[12px] font-medium transition ${
                isActive
                  ? "bg-brand-600/20 text-brand-300"
                  : "text-ink-300 hover:bg-white/5 hover:text-ink-100"
              }`
            }
          >
            <Icon className="h-4 w-4 shrink-0" />
            <span className="truncate">{label}</span>
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}

export function AppLayout() {
  const embed = useEmbedMode();

  return (
    <div
      className={`flex overflow-x-hidden bg-base-900 ${
        embed ? "h-[100dvh] max-h-[100dvh]" : "min-h-screen"
      }`}
    >
      <Sidebar embed={embed} />
      <div className="flex min-h-0 min-w-0 flex-1 flex-col">
        <header className="flex h-12 shrink-0 items-center justify-between gap-3 border-b border-white/8 bg-base-950/60 px-3 lg:px-4">
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
        <main
          className={`min-h-0 flex-1 overflow-x-hidden overflow-y-auto ${
            embed ? "px-3 py-3" : "px-5 py-5"
          }`}
        >
          <Outlet />
        </main>
      </div>
    </div>
  );
}
