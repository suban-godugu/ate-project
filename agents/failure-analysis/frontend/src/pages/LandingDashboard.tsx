import { Grid, Paper, Typography, Box, Alert, LinearProgress } from '@mui/material'
import { useQuery } from '@tanstack/react-query'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from 'recharts'
import { getWorkbenchOverview, listEvaluationRuns } from '../api/evaluationApi'
import { PageHeader, StatCard, MetricGauge } from '../components/common'

export default function LandingDashboard() {
  const { data: overview, isLoading } = useQuery({
    queryKey: ['workbench-overview'],
    queryFn: getWorkbenchOverview,
    refetchInterval: 10000,
  })
  const { data: runs } = useQuery({
    queryKey: ['evaluation-runs'],
    queryFn: () => listEvaluationRuns(5),
  })

  if (isLoading) return <LinearProgress />

  const health = overview?.ai_health_score ?? { score: 0, rating: 'N/A', factors: {} }
  const pf = overview?.latest_execution
  const passFailChart = [
    { name: 'PASS', count: pf?.pass_count ?? 0 },
    { name: 'WARN', count: pf?.warning_count ?? 0 },
    { name: 'FAIL', count: pf?.fail_count ?? 0 },
  ]

  return (
    <>
      <PageHeader
        title="Engineering Overview"
        subtitle="Real-time evaluation status for the Failure Analysis Agent"
      />

      {!overview?.production_readiness.production_ready && (
        <Alert severity="warning" sx={{ mb: 3 }}>
          Agent requires review before production deployment:{' '}
          {overview?.production_readiness.blockers.join('; ')}
        </Alert>
      )}

      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} md={3}>
          <Paper sx={{ p: 2, height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <MetricGauge score={health.score} rating={health.rating} />
          </Paper>
        </Grid>
        <Grid item xs={12} md={9}>
          <Grid container spacing={2}>
            <Grid item xs={6} sm={4} md={3}>
              <StatCard label="Total Datasets" value={overview?.total_datasets ?? 0} accent="#4fc3f7" />
            </Grid>
            <Grid item xs={6} sm={4} md={3}>
              <StatCard label="STIL Files" value={overview?.stil_count ?? 0} accent="#81c784" />
            </Grid>
            <Grid item xs={6} sm={4} md={3}>
              <StatCard label="Tester Logs" value={overview?.log_count ?? 0} accent="#ffb74d" />
            </Grid>
            <Grid item xs={6} sm={4} md={3}>
              <StatCard
                label="Overall Accuracy"
                value={`${((overview?.overall_accuracy ?? 0) * 100).toFixed(1)}%`}
                accent="#66bb6a"
              />
            </Grid>
            <Grid item xs={6} sm={4} md={3}>
              <StatCard
                label="Prediction Confidence"
                value={`${((overview?.overall_confidence ?? 0) * 100).toFixed(1)}%`}
              />
            </Grid>
            <Grid item xs={6} sm={4} md={3}>
              <StatCard label="CPU Usage" value={overview?.system_metrics.cpu_percent?.toFixed(1) ?? '—'} unit="%" />
            </Grid>
            <Grid item xs={6} sm={4} md={3}>
              <StatCard label="Memory" value={overview?.system_metrics.memory_mb?.toFixed(0) ?? '—'} unit="MB" />
            </Grid>
            <Grid item xs={6} sm={4} md={3}>
              <StatCard label="Model Version" value={overview?.latest_execution.model_version || 'n/a'} />
            </Grid>
          </Grid>
        </Grid>
      </Grid>

      <Grid container spacing={2}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              Validation Summary
            </Typography>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={passFailChart}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                <XAxis dataKey="name" stroke="#94a3b8" fontSize={12} />
                <YAxis stroke="#94a3b8" fontSize={12} />
                <Tooltip contentStyle={{ background: '#111827', border: '1px solid #333' }} />
                <Bar dataKey="count" fill="#4fc3f7" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              Current Status
            </Typography>
            <Box sx={{ display: 'grid', gap: 1.5, mt: 1 }}>
              <StatusRow label="Current Dataset" value={overview?.current_dataset ?? 'None'} />
              <StatusRow label="Agent Status" value={overview?.agent_status ?? '—'} />
              <StatusRow label="Database" value={overview?.database_health ?? '—'} />
              <StatusRow
                label="Latest Execution"
                value={overview?.latest_execution.execution_id?.slice(0, 8) ?? 'None'}
              />
              <StatusRow
                label="Processing Time"
                value={
                  overview?.latest_execution.processing_ms
                    ? `${(overview.latest_execution.processing_ms / 1000).toFixed(1)}s`
                    : '—'
                }
              />
            </Box>
          </Paper>
        </Grid>
        <Grid item xs={12}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              Recent Executions
            </Typography>
            {(runs?.runs ?? []).length === 0 ? (
              <Typography color="text.secondary" variant="body2">
                No evaluation runs yet. Go to Run Analysis to start.
              </Typography>
            ) : (
              <Box component="table" sx={{ width: '100%', borderCollapse: 'collapse', mt: 1 }}>
                <thead>
                  <tr>
                    {['Execution ID', 'Datasets', 'PASS', 'FAIL', 'WARN', 'Duration', 'Date'].map((h) => (
                      <th key={h} style={{ textAlign: 'left', padding: 8, color: '#94a3b8', fontSize: 12 }}>
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {runs?.runs.map((r) => (
                    <tr key={r.execution_id}>
                      <td style={{ padding: 8, fontFamily: 'monospace', fontSize: 13 }}>{r.execution_id.slice(0, 12)}…</td>
                      <td style={{ padding: 8 }}>{r.datasets_evaluated}</td>
                      <td style={{ padding: 8, color: '#66bb6a' }}>{r.pass_count}</td>
                      <td style={{ padding: 8, color: '#ef5350' }}>{r.fail_count}</td>
                      <td style={{ padding: 8, color: '#ffb74d' }}>{r.warning_count}</td>
                      <td style={{ padding: 8 }}>{(r.processing_ms / 1000).toFixed(1)}s</td>
                      <td style={{ padding: 8, fontSize: 12 }}>{r.created_at?.slice(0, 19) ?? '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </Box>
            )}
          </Paper>
        </Grid>
      </Grid>
    </>
  )
}

function StatusRow({ label, value }: { label: string; value: string }) {
  return (
    <Box sx={{ display: 'flex', justifyContent: 'space-between', py: 0.5, borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
      <Typography variant="body2" color="text.secondary">
        {label}
      </Typography>
      <Typography variant="body2" fontWeight={500}>
        {value}
      </Typography>
    </Box>
  )
}
