import { Grid, Paper, Typography, LinearProgress, Box } from '@mui/material'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
} from 'recharts'
import { useQuery } from '@tanstack/react-query'
import { getEvaluationReport, getWorkbenchOverview } from '../api/evaluationApi'
import { PageHeader, MetricGauge, StatCard, EmptyState } from '../components/common'
import { useWorkbench } from '../context/WorkbenchContext'

export default function AIEvaluation() {
  const { executionId } = useWorkbench()
  const { data: overview } = useQuery({ queryKey: ['workbench-overview'], queryFn: getWorkbenchOverview })
  const { data, isLoading } = useQuery({
    queryKey: ['evaluation-report', executionId],
    queryFn: () => getEvaluationReport(executionId ?? undefined),
  })

  if (isLoading) return <LinearProgress />

  const ai = data?.report?.dataset_results?.[0]?.ai_evaluation
  const health = overview?.ai_health_score ?? { score: 0, rating: 'N/A' }

  if (!ai) {
    return (
      <>
        <PageHeader title="AI Evaluation" subtitle="Pattern detection, classification, and prediction metrics" />
        <EmptyState message="Run an evaluation to view AI metrics." />
      </>
    )
  }

  const metrics = [
    { name: 'Accuracy', value: (ai.accuracy ?? 0) * 100 },
    { name: 'Precision', value: (ai.precision ?? 0) * 100 },
    { name: 'Recall', value: (ai.recall ?? 0) * 100 },
    { name: 'F1', value: (ai.f1_score ?? 0) * 100 },
    { name: 'Eng. Score', value: (ai.engineering_score ?? 0) * 100 },
    { name: 'Pred. Conf.', value: (ai.prediction_confidence ?? 0) * 100 },
  ]

  const radarData = metrics.map((m) => ({ metric: m.name, value: m.value }))

  return (
    <>
      <PageHeader title="AI Evaluation" subtitle="Accuracy, confidence, and engineering score analysis" />

      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} md={3}>
          <Paper sx={{ p: 3, display: 'flex', justifyContent: 'center' }}>
            <MetricGauge score={health.score} rating={health.rating} size={140} />
          </Paper>
        </Grid>
        <Grid item xs={12} md={9}>
          <Grid container spacing={2}>
            <Grid item xs={6} sm={4}>
              <StatCard label="Pattern Detection" value={`${((ai.accuracy ?? 0) * 100).toFixed(1)}%`} />
            </Grid>
            <Grid item xs={6} sm={4}>
              <StatCard label="Classification" value={`${((ai.precision ?? 0) * 100).toFixed(1)}%`} accent="#81c784" />
            </Grid>
            <Grid item xs={6} sm={4}>
              <StatCard label="Root Cause Pred." value={`${((ai.prediction_confidence ?? 0) * 100).toFixed(1)}%`} />
            </Grid>
            <Grid item xs={6} sm={4}>
              <StatCard label="Recommendation Acc." value={`${((ai.recommendation_accuracy ?? 0) * 100).toFixed(1)}%`} />
            </Grid>
            <Grid item xs={6} sm={4}>
              <StatCard label="Similarity Acc." value={`${((ai.similarity_accuracy ?? 0) * 100).toFixed(1)}%`} />
            </Grid>
            <Grid item xs={6} sm={4}>
              <StatCard label="F1 Score" value={(ai.f1_score ?? 0).toFixed(3)} />
            </Grid>
          </Grid>
        </Grid>
      </Grid>

      <Grid container spacing={2}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              AI Metrics Comparison
            </Typography>
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={metrics}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                <XAxis dataKey="name" stroke="#94a3b8" fontSize={11} />
                <YAxis domain={[0, 100]} stroke="#94a3b8" fontSize={11} />
                <Tooltip contentStyle={{ background: '#111827', border: '1px solid #333' }} />
                <Bar dataKey="value" fill="#4fc3f7" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              AI Health Radar
            </Typography>
            <ResponsiveContainer width="100%" height={280}>
              <RadarChart data={radarData}>
                <PolarGrid stroke="rgba(255,255,255,0.1)" />
                <PolarAngleAxis dataKey="metric" tick={{ fill: '#94a3b8', fontSize: 11 }} />
                <PolarRadiusAxis domain={[0, 100]} tick={{ fill: '#64748b', fontSize: 10 }} />
                <Radar dataKey="value" stroke="#4fc3f7" fill="#4fc3f7" fillOpacity={0.3} />
              </RadarChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>
        {ai.confusion_matrix && (
          <Grid item xs={12}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="subtitle2" gutterBottom>
                Confusion Matrix
              </Typography>
              <Box sx={{ overflow: 'auto' }}>
                <table style={{ borderCollapse: 'collapse', fontSize: 13 }}>
                  <thead>
                    <tr>
                      <th style={{ padding: 8 }} />
                      {ai.confusion_matrix.labels.map((l) => (
                        <th key={l} style={{ padding: 8, color: '#94a3b8' }}>
                          {l}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {ai.confusion_matrix.matrix.map((row, i) => (
                      <tr key={i}>
                        <td style={{ padding: 8, color: '#94a3b8' }}>{ai.confusion_matrix!.labels[i]}</td>
                        {row.map((v, j) => (
                          <td
                            key={j}
                            style={{
                              padding: 8,
                              textAlign: 'center',
                              background: `rgba(79,195,247,${Math.min(v / 10, 0.8)})`,
                            }}
                          >
                            {v}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </Box>
            </Paper>
          </Grid>
        )}
      </Grid>
    </>
  )
}
