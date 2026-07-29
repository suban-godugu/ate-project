import { Grid, Paper, Typography, Button, Box, LinearProgress, Alert } from '@mui/material'
import DownloadIcon from '@mui/icons-material/Download'
import { useQuery } from '@tanstack/react-query'
import { getEvaluationReport, exportDownloadUrl } from '../api/evaluationApi'
import { PageHeader, EmptyState } from '../components/common'
import { useWorkbench } from '../context/WorkbenchContext'

const REPORT_TYPES = [
  { id: 'engineering', fmt: 'pdf', label: 'Engineering Report', desc: 'Full technical analysis for engineering teams' },
  { id: 'executive', fmt: 'pdf', label: 'Executive Summary', desc: 'High-level readiness and accuracy overview' },
  { id: 'validation', fmt: 'pdf', label: 'Validation Report', desc: 'FA-FR-001–010 functional requirement results' },
  { id: 'performance', fmt: 'excel', label: 'Performance Report', desc: 'Stage timing and resource utilization' },
  { id: 'benchmark', fmt: 'excel', label: 'Benchmark Report', desc: 'Cross-dataset benchmark comparison' },
  { id: 'prediction', fmt: 'csv', label: 'Prediction Report', desc: 'AI prediction outputs and confidence scores' },
]

const FORMATS = ['pdf', 'excel', 'csv', 'json'] as const

export default function ReportsScreen() {
  const { executionId } = useWorkbench()
  const { data, isLoading } = useQuery({
    queryKey: ['evaluation-report', executionId],
    queryFn: () => getEvaluationReport(executionId ?? undefined),
  })

  const execId = executionId ?? data?.execution_id

  if (isLoading) return <LinearProgress />

  if (!execId) {
    return (
      <>
        <PageHeader title="Reports" subtitle="Export engineering, validation, and benchmark reports" />
        <EmptyState message="No evaluation run selected. Run an analysis first." />
      </>
    )
  }

  const exportPaths = data?.export_paths ?? {}

  return (
    <>
      <PageHeader
        title="Reports"
        subtitle="Export evaluation artifacts in PDF, Excel, CSV, and JSON formats"
      />

      <Alert severity="info" sx={{ mb: 3 }}>
        Execution ID: <strong>{execId}</strong>
        {data?.report?.processing_ms != null && (
          <> — completed in {(data.report.processing_ms / 1000).toFixed(1)}s</>
        )}
      </Alert>

      <Grid container spacing={2} sx={{ mb: 4 }}>
        {REPORT_TYPES.map(({ id, fmt, label, desc }) => (
          <Grid item xs={12} sm={6} md={4} key={id}>
            <Paper sx={{ p: 2, height: '100%', display: 'flex', flexDirection: 'column' }}>
              <Typography variant="subtitle1" fontWeight={600} gutterBottom>
                {label}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ flex: 1, mb: 2 }}>
                {desc}
              </Typography>
              <Button
                variant="outlined"
                size="small"
                startIcon={<DownloadIcon />}
                href={exportDownloadUrl(fmt, execId)}
                target="_blank"
              >
                Download {fmt.toUpperCase()}
              </Button>
            </Paper>
          </Grid>
        ))}
      </Grid>

      <Paper sx={{ p: 2 }}>
        <Typography variant="subtitle2" gutterBottom>
          Bulk Export
        </Typography>
        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
          {FORMATS.map((fmt) => (
            <Button
              key={fmt}
              variant="contained"
              size="small"
              startIcon={<DownloadIcon />}
              href={exportDownloadUrl(fmt, execId)}
              target="_blank"
              disabled={exportPaths[fmt] === null}
            >
              {fmt.toUpperCase()}
            </Button>
          ))}
        </Box>
      </Paper>
    </>
  )
}
