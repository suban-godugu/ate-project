import { Grid, Paper, Typography, LinearProgress, Chip } from '@mui/material'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  Cell,
} from 'recharts'
import { useQuery } from '@tanstack/react-query'
import { getEvaluationReport, getWorkbenchOverview } from '../api/evaluationApi'
import { PageHeader, StatCard, EmptyState } from '../components/common'
import { useWorkbench } from '../context/WorkbenchContext'

const STAGE_LABELS: Record<string, string> = {
  upload: 'Upload / Parse',
  parsing: 'STIL Parsing',
  pattern_detection: 'Pattern Detection',
  failure_rates: 'Failure Rates',
  classification: 'Classification',
  recurring: 'Recurring Detection',
  correlation: 'Correlation',
  die_analysis: 'Die Analysis',
  wafer_analysis: 'Wafer Analysis',
  root_cause: 'Root Cause Prediction',
  report_generation: 'Report Generation',
}

export default function PerformanceDashboard() {
  const { executionId } = useWorkbench()
  const { data: overview } = useQuery({ queryKey: ['workbench-overview'], queryFn: getWorkbenchOverview })
  const { data, isLoading } = useQuery({
    queryKey: ['evaluation-report', executionId],
    queryFn: () => getEvaluationReport(executionId ?? undefined),
  })

  if (isLoading) return <LinearProgress />

  const stages = data?.report?.dataset_results?.flatMap((d) => d.benchmark?.stages ?? []) ?? []
  const chartData = stages.map((s) => ({
    name: STAGE_LABELS[s.name] ?? s.name,
    ms: s.avg_ms,
    meets: s.meets_target,
  }))

  const sys = overview?.system_metrics

  return (
    <>
      <PageHeader title="Performance Dashboard" subtitle="Pipeline timing, resource usage, and bottlenecks" />

      {stages.length === 0 ? (
        <EmptyState message="No benchmark data. Run an evaluation first." />
      ) : (
        <>
          <Grid container spacing={2} sx={{ mb: 3 }}>
            <Grid item xs={6} sm={3}>
              <StatCard label="Total Pipeline" value={`${(stages.reduce((a, s) => a + s.avg_ms, 0) / 1000).toFixed(1)}s`} />
            </Grid>
            <Grid item xs={6} sm={3}>
              <StatCard label="CPU" value={sys?.cpu_percent?.toFixed(1) ?? '—'} unit="%" />
            </Grid>
            <Grid item xs={6} sm={3}>
              <StatCard label="Memory" value={sys?.memory_mb?.toFixed(0) ?? '—'} unit="MB" />
            </Grid>
            <Grid item xs={6} sm={3}>
              <StatCard label="Disk Usage" value={sys?.disk_usage_percent?.toFixed(1) ?? '—'} unit="%" />
            </Grid>
          </Grid>

          <Paper sx={{ p: 2, mb: 3 }}>
            <Typography variant="subtitle2" gutterBottom>
              Stage Execution Time (ms)
            </Typography>
            <ResponsiveContainer width="100%" height={320}>
              <BarChart data={chartData} layout="vertical" margin={{ left: 120 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                <XAxis type="number" stroke="#94a3b8" fontSize={11} />
                <YAxis type="category" dataKey="name" stroke="#94a3b8" fontSize={11} width={110} />
                <Tooltip contentStyle={{ background: '#111827', border: '1px solid #333' }} />
                <Bar dataKey="ms" radius={[0, 4, 4, 0]}>
                  {chartData.map((entry, i) => (
                    <Cell key={i} fill={entry.meets === false ? '#ef5350' : '#4fc3f7'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </Paper>

          <Paper sx={{ p: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              Stage Details
            </Typography>
            {stages.map((s) => (
              <Grid container key={s.name} sx={{ py: 1, borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                <Grid item xs={4}>
                  <Typography variant="body2">{STAGE_LABELS[s.name] ?? s.name}</Typography>
                </Grid>
                <Grid item xs={2}>
                  <Typography variant="body2">{s.avg_ms.toFixed(0)} ms avg</Typography>
                </Grid>
                <Grid item xs={2}>
                  <Typography variant="body2" color="text.secondary">
                    max {s.max_ms?.toFixed(0) ?? '—'} ms
                  </Typography>
                </Grid>
                <Grid item xs={2}>
                  <Chip
                    label={s.meets_target === false ? 'Over threshold' : 'OK'}
                    size="small"
                    color={s.meets_target === false ? 'error' : 'success'}
                    variant="outlined"
                  />
                </Grid>
              </Grid>
            ))}
          </Paper>
        </>
      )}
    </>
  )
}
