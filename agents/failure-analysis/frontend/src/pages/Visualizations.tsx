import { Grid, Paper, Typography, LinearProgress, Box } from '@mui/material'
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  PieChart,
  Pie,
  Cell,
} from 'recharts'
import Plot from 'react-plotly.js'
import { useQuery } from '@tanstack/react-query'
import {
  getEvaluationDashboard,
  getWorkbenchVisualizations,
} from '../api/evaluationApi'
import { PageHeader, EmptyState } from '../components/common'
import { useWorkbench } from '../context/WorkbenchContext'

const PIE_COLORS = ['#4fc3f7', '#81c784', '#ffb74d', '#ef5350', '#ba68c8', '#64b5f6']

function ChartCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <Paper sx={{ p: 2, height: '100%' }}>
      <Typography variant="subtitle2" gutterBottom>
        {title}
      </Typography>
      {children}
    </Paper>
  )
}

export default function Visualizations() {
  const { executionId } = useWorkbench()
  const { data: vizData, isLoading: vizLoading } = useQuery({
    queryKey: ['workbench-viz', executionId],
    queryFn: () => getWorkbenchVisualizations(executionId ?? undefined),
  })
  const { data: dash, isLoading: dashLoading } = useQuery({
    queryKey: ['evaluation-dashboard', executionId],
    queryFn: () => getEvaluationDashboard(executionId ?? undefined),
  })

  if (vizLoading || dashLoading) return <LinearProgress />

  const charts = vizData?.visualizations?.charts ?? dash?.dashboard?.charts ?? {}
  const confusion = vizData?.visualizations?.confusion_matrix
  const chartEntries = Object.entries(charts)

  if (chartEntries.length === 0 && !confusion) {
    return (
      <>
        <PageHeader title="Visualizations" subtitle="Failure heatmaps, trends, and correlation graphs" />
        <EmptyState message="No visualization data. Run an evaluation to generate charts." />
      </>
    )
  }

  const renderChart = (key: string, chart: { type: string; x: string[]; y: number[] }) => {
    const data = chart.x.map((label, i) => ({ label, value: chart.y[i] ?? 0 }))
    if (chart.type === 'pie' || key.includes('distribution')) {
      return (
        <ResponsiveContainer width="100%" height={260}>
          <PieChart>
            <Pie data={data} dataKey="value" nameKey="label" cx="50%" cy="50%" outerRadius={90}>
              {data.map((_, i) => (
                <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
              ))}
            </Pie>
            <Tooltip contentStyle={{ background: '#111827', border: '1px solid #333' }} />
          </PieChart>
        </ResponsiveContainer>
      )
    }
    if (chart.type === 'line' || key.includes('trend')) {
      return (
        <ResponsiveContainer width="100%" height={260}>
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
            <XAxis dataKey="label" stroke="#94a3b8" fontSize={10} />
            <YAxis stroke="#94a3b8" fontSize={11} />
            <Tooltip contentStyle={{ background: '#111827', border: '1px solid #333' }} />
            <Line type="monotone" dataKey="value" stroke="#4fc3f7" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      )
    }
    return (
      <ResponsiveContainer width="100%" height={260}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
          <XAxis dataKey="label" stroke="#94a3b8" fontSize={10} />
          <YAxis stroke="#94a3b8" fontSize={11} />
          <Tooltip contentStyle={{ background: '#111827', border: '1px solid #333' }} />
          <Bar dataKey="value" fill="#4fc3f7" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    )
  }

  const heatmapFromConfusion = confusion
    ? {
        z: confusion.matrix,
        x: confusion.labels,
        y: confusion.labels,
        type: 'heatmap' as const,
        colorscale: 'Blues',
      }
    : null

  return (
    <>
      <PageHeader
        title="Visualizations"
        subtitle="Failure heatmaps, pattern frequency, trends, and correlation analysis"
      />

      <Grid container spacing={2}>
        {chartEntries.map(([key, chart]) => (
          <Grid item xs={12} md={6} key={key}>
            <ChartCard title={key.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())}>
              {renderChart(key, chart)}
            </ChartCard>
          </Grid>
        ))}

        {heatmapFromConfusion && (
          <Grid item xs={12} md={6}>
            <ChartCard title="Classification Confusion Heatmap">
              <Box sx={{ height: 280 }}>
                <Plot
                  data={[heatmapFromConfusion]}
                  layout={{
                    paper_bgcolor: 'transparent',
                    plot_bgcolor: 'transparent',
                    font: { color: '#94a3b8', size: 11 },
                    margin: { t: 20, b: 60, l: 60, r: 20 },
                    xaxis: { tickangle: -45 },
                  }}
                  config={{ displayModeBar: false, responsive: true }}
                  style={{ width: '100%', height: '100%' }}
                />
              </Box>
            </ChartCard>
          </Grid>
        )}
      </Grid>
    </>
  )
}
