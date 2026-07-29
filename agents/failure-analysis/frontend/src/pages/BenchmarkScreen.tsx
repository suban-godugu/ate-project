import { Grid, Paper, Typography, LinearProgress, Chip, Box } from '@mui/material'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  Legend,
} from 'recharts'
import { useQuery } from '@tanstack/react-query'
import { listEvaluationRuns, getEvaluationReport } from '../api/evaluationApi'
import { PageHeader, EmptyState } from '../components/common'

const SCALE_ORDER = ['1000', '2000', '29642', 'full']

function scaleLabel(datasetId: string): string {
  for (const s of SCALE_ORDER) {
    if (datasetId.includes(s)) return `${s} patterns`
  }
  return datasetId
}

export default function BenchmarkScreen() {
  const { data: runsData, isLoading: runsLoading } = useQuery({
    queryKey: ['evaluation-runs-benchmark'],
    queryFn: () => listEvaluationRuns(20),
  })

  const runs = runsData?.runs ?? []
  const latestId = runs[0]?.execution_id

  const { data: report, isLoading: reportLoading } = useQuery({
    queryKey: ['benchmark-report', latestId],
    queryFn: () => getEvaluationReport(latestId),
    enabled: !!latestId,
  })

  if (runsLoading || reportLoading) return <LinearProgress />

  const datasetResults = report?.report?.dataset_results ?? []

  if (datasetResults.length === 0 && runs.length === 0) {
    return (
      <>
        <PageHeader title="Benchmark" subtitle="Compare performance across 1000, 2000, and full-scale datasets" />
        <EmptyState message="No benchmark runs available. Execute evaluations on each dataset scale." />
      </>
    )
  }

  const timingData = datasetResults.map((ds) => ({
    name: scaleLabel(ds.dataset?.dataset_id ?? 'unknown'),
    totalMs: ds.benchmark?.stages?.reduce((a, s) => a + s.avg_ms, 0) ?? 0,
    logs: ds.logs_evaluated,
  }))

  const accuracyData = datasetResults.map((ds) => ({
    name: scaleLabel(ds.dataset?.dataset_id ?? 'unknown'),
    accuracy: (ds.ai_evaluation?.accuracy ?? 0) * 100,
    f1: (ds.ai_evaluation?.f1_score ?? 0) * 100,
    confidence: (ds.ai_evaluation?.prediction_confidence ?? 0) * 100,
  }))

  const runHistory = runs.slice(0, 10).map((r) => ({
    name: r.execution_id.slice(0, 8),
    ms: r.processing_ms / 1000,
    pass: r.pass_count,
    fail: r.fail_count,
  }))

  return (
    <>
      <PageHeader
        title="Benchmark Comparison"
        subtitle="Execution time, accuracy, and resource usage across dataset scales"
      />

      <Grid container spacing={2} sx={{ mb: 3 }}>
        {runs.slice(0, 3).map((r) => (
          <Grid item xs={12} md={4} key={r.execution_id}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="caption" color="text.secondary">
                Run {r.execution_id.slice(0, 12)}…
              </Typography>
              <Typography variant="h6">{(r.processing_ms / 1000).toFixed(1)}s</Typography>
              <Typography variant="body2" color="text.secondary">
                {r.datasets_evaluated} datasets · {r.model_version}
              </Typography>
              <Box sx={{ mt: 1, display: 'flex', gap: 0.5 }}>
                <Chip label={`${r.pass_count} PASS`} size="small" color="success" variant="outlined" />
                <Chip label={`${r.warning_count} WARN`} size="small" color="warning" variant="outlined" />
                <Chip label={`${r.fail_count} FAIL`} size="small" color="error" variant="outlined" />
              </Box>
            </Paper>
          </Grid>
        ))}
      </Grid>

      <Grid container spacing={2}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              Pipeline Time by Dataset Scale (ms)
            </Typography>
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={timingData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                <XAxis dataKey="name" stroke="#94a3b8" fontSize={11} />
                <YAxis stroke="#94a3b8" fontSize={11} />
                <Tooltip contentStyle={{ background: '#111827', border: '1px solid #333' }} />
                <Bar dataKey="totalMs" fill="#4fc3f7" name="Total ms" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              AI Accuracy by Dataset Scale (%)
            </Typography>
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={accuracyData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                <XAxis dataKey="name" stroke="#94a3b8" fontSize={11} />
                <YAxis domain={[0, 100]} stroke="#94a3b8" fontSize={11} />
                <Tooltip contentStyle={{ background: '#111827', border: '1px solid #333' }} />
                <Legend />
                <Bar dataKey="accuracy" fill="#66bb6a" name="Accuracy" />
                <Bar dataKey="f1" fill="#4fc3f7" name="F1" />
                <Bar dataKey="confidence" fill="#ffb74d" name="Confidence" />
              </BarChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>
        <Grid item xs={12}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              Recent Run History (seconds)
            </Typography>
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={runHistory}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                <XAxis dataKey="name" stroke="#94a3b8" fontSize={11} />
                <YAxis stroke="#94a3b8" fontSize={11} />
                <Tooltip contentStyle={{ background: '#111827', border: '1px solid #333' }} />
                <Bar dataKey="ms" fill="#81c784" name="Duration (s)" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>
      </Grid>
    </>
  )
}
