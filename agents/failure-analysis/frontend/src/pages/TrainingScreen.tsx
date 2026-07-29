import {
  Grid,
  Paper,
  Typography,
  LinearProgress,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Alert,
} from '@mui/material'
import { useQuery } from '@tanstack/react-query'
import { getEvaluationReport } from '../api/evaluationApi'
import { PageHeader, StatCard, EmptyState } from '../components/common'
import { useWorkbench } from '../context/WorkbenchContext'

export default function TrainingScreen() {
  const { executionId } = useWorkbench()
  const { data, isLoading } = useQuery({
    queryKey: ['evaluation-report', executionId],
    queryFn: () => getEvaluationReport(executionId ?? undefined),
  })

  if (isLoading) return <LinearProgress />

  const training =
    data?.report?.latest_training ??
    data?.report?.dataset_results?.find((d) => d.training?.trained)?.training

  if (!training) {
    return (
      <>
        <PageHeader title="AI Training" subtitle="Model training, retraining, and version comparison" />
        <EmptyState message="No training data. Labelled datasets are required for model training." />
      </>
    )
  }

  const comparisons = training.comparisons ?? []

  return (
    <>
      <PageHeader
        title="AI Training"
        subtitle="Train, retrain, and compare ML models on labelled failure datasets"
      />

      {!training.trained && training.reason && (
        <Alert severity="info" sx={{ mb: 3 }}>
          {training.reason}
        </Alert>
      )}

      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={6} sm={3}>
          <StatCard
            label="Model"
            value={training.model_name ?? '—'}
            accent="#4fc3f7"
          />
        </Grid>
        <Grid item xs={6} sm={3}>
          <StatCard label="Version" value={training.model_version ?? '—'} />
        </Grid>
        <Grid item xs={6} sm={3}>
          <StatCard
            label="Validation Accuracy"
            value={
              training.validation_accuracy != null
                ? `${(training.validation_accuracy * 100).toFixed(1)}%`
                : '—'
            }
            accent="#66bb6a"
          />
        </Grid>
        <Grid item xs={6} sm={3}>
          <StatCard label="Training Samples" value={training.sample_count ?? '—'} />
        </Grid>
      </Grid>

      {comparisons.length > 0 && (
        <Paper sx={{ overflow: 'auto' }}>
          <Typography variant="subtitle2" sx={{ p: 2, pb: 0 }}>
            Model Comparison
          </Typography>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Model</TableCell>
                <TableCell>Validation Acc.</TableCell>
                <TableCell>Test Acc.</TableCell>
                <TableCell>Status</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {comparisons.map((c, i) => (
                <TableRow key={i}>
                  <TableCell>{c.model}</TableCell>
                  <TableCell>
                    {c.validation_accuracy != null
                      ? `${(c.validation_accuracy * 100).toFixed(1)}%`
                      : '—'}
                  </TableCell>
                  <TableCell>
                    {c.test_accuracy != null ? `${(c.test_accuracy * 100).toFixed(1)}%` : '—'}
                  </TableCell>
                  <TableCell>{c.error ?? 'OK'}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Paper>
      )}
    </>
  )
}
