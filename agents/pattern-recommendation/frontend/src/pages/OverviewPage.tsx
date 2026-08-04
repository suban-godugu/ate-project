import { useMemo } from 'react'
import {
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  Bar,
  BarChart,
  XAxis,
  YAxis,
  CartesianGrid,
} from 'recharts'
import {
  Activity,
  Boxes,
  CircleAlert,
  Database,
  Layers,
  Sparkles,
} from 'lucide-react'
import { StatCard } from '@/components/StatCard'
import { useDashboardStore } from '@/contexts/dashboardStore'
import { useEmbedMode } from '@/hooks/useEmbedMode'
import { formatBuiltAt } from '@/utils/format'

const PIE_COLORS = ['#8b5cf6', '#34d399', '#f59e0b', '#f43f5e']

export function OverviewPage() {
  const embed = useEmbedMode()
  const failure = useDashboardStore((s) => s.failure)
  const summary = useDashboardStore((s) => s.summary)
  const patternStats = useDashboardStore((s) => s.patternStats)
  const datasets = useDashboardStore((s) => s.datasets)
  const healthOk = useDashboardStore((s) => s.healthOk)
  const dashboard = useDashboardStore((s) => s.dashboard)

  const failSummary = failure?.summary
  const avgFail =
    patternStats?.average_fail_rate != null
      ? `${(patternStats.average_fail_rate * 100).toFixed(2)}%`
      : '—'
  const avgToggle =
    patternStats?.average_toggle_density != null
      ? patternStats.average_toggle_density.toFixed(4)
      : '—'

  const severityData = useMemo(
    () => [
      { name: 'HIGH', value: failSummary?.severity_high ?? 0 },
      { name: 'MEDIUM', value: failSummary?.severity_medium ?? 0 },
      { name: 'LOW', value: failSummary?.severity_low ?? 0 },
    ],
    [failSummary],
  )

  const domainData = useMemo(
    () => [
      { name: 'Removal', value: summary?.removal_candidates ?? 0 },
      { name: 'Ordering', value: summary?.ordering_candidates ?? 0 },
      { name: 'Gaps', value: summary?.gap_requests ?? 0 },
      { name: 'Low-power', value: summary?.low_power_patterns ?? 0 },
      { name: 'Coverage', value: summary?.coverage_recommendations ?? 0 },
    ],
    [summary],
  )

  const sectionGap = embed ? 'space-y-3' : 'space-y-6'
  const heading = embed
    ? 'mb-1.5 text-[10px] font-semibold uppercase tracking-[0.08em] text-ink-400'
    : 'mb-3 text-sm font-semibold uppercase tracking-[0.08em] text-ink-400'
  const gridGap = embed ? 'gap-2' : 'gap-3'
  const chartH = embed ? 'h-36' : 'h-64'
  const chartPad = embed ? 'card-surface rounded-xl p-2.5' : 'card-surface p-4'

  return (
    <div className={`min-w-0 overflow-x-hidden ${sectionGap} ${embed ? 'px-3 py-3' : ''}`}>
      <section>
        <h2 className={heading}>Failure health</h2>
        <div
          className={`grid min-w-0 ${gridGap} grid-cols-2 sm:grid-cols-3 ${
            embed ? 'lg:grid-cols-5' : 'xl:grid-cols-5'
          }`}
        >
          <StatCard
            compact={embed}
            label="Total logs"
            value={failSummary?.total_logs ?? '—'}
            to="/failures"
            icon={Activity}
          />
          <StatCard
            compact={embed}
            label="Failed / Good"
            value={`${failSummary?.failed_logs ?? '—'} / ${failSummary?.good_logs ?? '—'}`}
            to="/failures"
            icon={CircleAlert}
          />
          <StatCard
            compact={embed}
            label="Unique failing patterns"
            value={failSummary?.unique_patterns ?? '—'}
            to="/failures"
          />
          <StatCard
            compact={embed}
            label="Lots covered"
            value={failSummary?.total_lots ?? '—'}
            to="/failures"
          />
          <StatCard
            compact={embed}
            label="Severity mix"
            value={`H ${failSummary?.severity_high ?? 0} · M ${failSummary?.severity_medium ?? 0} · L ${failSummary?.severity_low ?? 0}`}
            sublabel="HIGH / MEDIUM / LOW"
            to="/failures"
            accent
          />
        </div>
      </section>

      <section>
        <h2 className={heading}>Pattern analytics</h2>
        <div
          className={`grid min-w-0 ${gridGap} grid-cols-2 ${
            embed ? 'lg:grid-cols-4' : 'sm:grid-cols-2 xl:grid-cols-4'
          }`}
        >
          <StatCard
            compact={embed}
            label="Patterns analyzed"
            value={summary?.patterns_analyzed ?? patternStats?.patterns ?? '—'}
            icon={Sparkles}
          />
          <StatCard
            compact={embed}
            label="Clusters"
            value={summary?.clusters ?? '—'}
            to="/redundancy"
            icon={Boxes}
          />
          <StatCard compact={embed} label="Avg fail rate" value={avgFail} />
          <StatCard compact={embed} label="Avg toggle density" value={avgToggle} />
        </div>
      </section>

      <section>
        <h2 className={heading}>Recommendation domains</h2>
        <div
          className={`grid min-w-0 ${gridGap} grid-cols-2 sm:grid-cols-3 ${
            embed ? 'lg:grid-cols-5' : 'xl:grid-cols-5'
          }`}
        >
          <StatCard
            compact={embed}
            label="Removal candidates"
            value={summary?.removal_candidates ?? '—'}
            sublabel="full"
            to="/removal"
          />
          <StatCard
            compact={embed}
            label="Ordering candidates"
            value={summary?.ordering_candidates ?? '—'}
            sublabel="full"
            to="/ordering"
          />
          <StatCard
            compact={embed}
            label="ATPG gap requests"
            value={summary?.gap_requests ?? '—'}
            sublabel="gap_requests_only"
            to="/gap"
          />
          <StatCard
            compact={embed}
            label="Low-power set"
            value={summary?.low_power_patterns ?? '—'}
            sublabel="toggle_activity_proxy"
            to="/low-power"
          />
          <StatCard
            compact={embed}
            label="Coverage recs"
            value={summary?.coverage_recommendations ?? '—'}
            sublabel="toggle_fail_proxy"
            to="/coverage"
          />
        </div>
      </section>

      <section>
        <h2 className={heading}>Data readiness</h2>
        <div className={`grid min-w-0 ${gridGap} grid-cols-3`}>
          <StatCard
            compact={embed}
            label="Datasets"
            value={`${datasets?.available ?? '—'} / ${datasets?.missing ?? '—'} / ${datasets?.invalid ?? '—'}`}
            sublabel="available · missing · invalid"
            to="/settings"
            icon={Database}
          />
          <StatCard
            compact={embed}
            label="API status"
            value={healthOk ? 'healthy' : 'down'}
            icon={Layers}
          />
          <StatCard
            compact={embed}
            label="Last built"
            value={formatBuiltAt(dashboard?.built_at)}
          />
        </div>
      </section>

      <section className={`grid min-w-0 ${embed ? 'gap-2' : 'gap-4'} lg:grid-cols-2`}>
        <div className={chartPad}>
          <h3
            className={`font-semibold text-ink-100 ${
              embed ? 'mb-1.5 text-xs' : 'mb-3 text-sm'
            }`}
          >
            Severity distribution
          </h3>
          <div className={chartH}>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={severityData}
                  dataKey="value"
                  nameKey="name"
                  innerRadius={embed ? 32 : 55}
                  outerRadius={embed ? 52 : 90}
                  paddingAngle={3}
                >
                  {severityData.map((_, i) => (
                    <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    background: '#1a102c',
                    border: '1px solid rgba(255,255,255,0.1)',
                    borderRadius: 12,
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
        <div className={chartPad}>
          <h3
            className={`font-semibold text-ink-100 ${
              embed ? 'mb-1.5 text-xs' : 'mb-3 text-sm'
            }`}
          >
            Recommendation volume
          </h3>
          <div className={chartH}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={domainData}>
                <CartesianGrid stroke="rgba(255,255,255,0.06)" vertical={false} />
                <XAxis
                  dataKey="name"
                  stroke="#7d6f96"
                  tick={{ fontSize: embed ? 10 : 12 }}
                />
                <YAxis stroke="#7d6f96" tick={{ fontSize: embed ? 10 : 12 }} />
                <Tooltip
                  contentStyle={{
                    background: '#1a102c',
                    border: '1px solid rgba(255,255,255,0.1)',
                    borderRadius: 12,
                  }}
                />
                <Bar dataKey="value" fill="#8b5cf6" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </section>
    </div>
  )
}
