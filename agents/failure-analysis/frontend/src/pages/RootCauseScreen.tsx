import {
  Box,
  Grid,
  Paper,
  Typography,
  LinearProgress,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Chip,
} from '@mui/material'
import ExpandMoreIcon from '@mui/icons-material/ExpandMore'
import { useQuery } from '@tanstack/react-query'
import { getRootCauseHistory, getRootCauseRecommendations, getEvaluationReport } from '../api/evaluationApi'
import { PageHeader, EmptyState } from '../components/common'
import { useWorkbench } from '../context/WorkbenchContext'

interface PredictionRow {
  pattern_id?: string
  failure_type?: string
  predicted_root_cause?: string
  confidence?: number
  explanation?: string
  supporting_evidence?: string[]
}

export default function RootCauseScreen() {
  const { executionId } = useWorkbench()
  const { data: history, isLoading: histLoading, isError: histError } = useQuery({
    queryKey: ['root-cause-history'],
    queryFn: getRootCauseHistory,
    retry: false,
  })
  const { data: recs, isLoading: recLoading, isError: recError } = useQuery({
    queryKey: ['root-cause-recommendations'],
    queryFn: getRootCauseRecommendations,
    retry: false,
  })
  const { data: report } = useQuery({
    queryKey: ['evaluation-report', executionId],
    queryFn: () => getEvaluationReport(executionId ?? undefined),
  })

  const evalRc = report?.report?.dataset_results?.[0]?.module_outputs?.['FA-FR-009'] as
    | Record<string, unknown>
    | undefined

  const predictions = (history?.predictions ?? []) as PredictionRow[]
  const similarCases = (history?.similar_historical_cases ?? []) as Record<string, unknown>[]
  const recommendations = (recs?.engineering_recommendations ?? []) as Record<string, unknown>[]
  const explanations = (recs?.ai_explanations ?? []) as Record<string, unknown>[]

  const loading = histLoading || recLoading
  const hasData = predictions.length > 0 || evalRc || !histError

  if (loading) return <LinearProgress />

  if (!hasData && histError && recError) {
    return (
      <>
        <PageHeader title="Root Cause Analysis" subtitle="Predicted root causes and engineering recommendations" />
        <EmptyState message="No root cause predictions available. Run FA-FR-009 via evaluation or upload data." />
      </>
    )
  }

  return (
    <>
      <PageHeader
        title="Root Cause Analysis"
        subtitle="AI predictions, confidence scores, and engineering investigation guidance"
      />

      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={6} sm={3}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="subtitle2" color="text.secondary">
              Total Predictions
            </Typography>
            <Typography variant="h5">
              {(history?.total_predictions as number) ?? (evalRc?.total_predictions as number) ?? '—'}
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={6} sm={3}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="subtitle2" color="text.secondary">
              Avg Confidence
            </Typography>
            <Typography variant="h5">
              {history?.average_confidence
                ? `${((history.average_confidence as number) * 100).toFixed(1)}%`
                : '—'}
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={6} sm={3}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="subtitle2" color="text.secondary">
              High Confidence
            </Typography>
            <Typography variant="h5">{(history?.high_confidence_count as number) ?? '—'}</Typography>
          </Paper>
        </Grid>
        <Grid item xs={6} sm={3}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="subtitle2" color="text.secondary">
              ML Model
            </Typography>
            <Typography variant="h5">
              {history?.ml_model_trained ? 'Trained' : evalRc ? 'Evaluated' : '—'}
            </Typography>
          </Paper>
        </Grid>
      </Grid>

      {predictions.length > 0 && (
        <Paper sx={{ mb: 3, overflow: 'auto' }}>
          <Typography variant="subtitle2" sx={{ p: 2, pb: 0 }}>
            Predicted Root Causes
          </Typography>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Pattern</TableCell>
                <TableCell>Failure</TableCell>
                <TableCell>Root Cause</TableCell>
                <TableCell>Confidence</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {predictions.slice(0, 50).map((p, i) => (
                <TableRow key={i}>
                  <TableCell>{p.pattern_id ?? '—'}</TableCell>
                  <TableCell>{p.failure_type ?? '—'}</TableCell>
                  <TableCell>{p.predicted_root_cause ?? '—'}</TableCell>
                  <TableCell>
                    {p.confidence != null ? (
                      <Chip
                        label={`${(p.confidence * 100).toFixed(0)}%`}
                        size="small"
                        color={p.confidence >= 0.8 ? 'success' : p.confidence >= 0.5 ? 'warning' : 'default'}
                        variant="outlined"
                      />
                    ) : (
                      '—'
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Paper>
      )}

      {similarCases.length > 0 && (
        <Paper sx={{ p: 2, mb: 3 }}>
          <Typography variant="subtitle2" gutterBottom>
            Historical Similar Cases
          </Typography>
          {similarCases.slice(0, 10).map((c, i) => (
            <Typography key={i} variant="body2" color="text.secondary" sx={{ py: 0.5 }}>
              {String(c.case_id ?? c.pattern_id ?? JSON.stringify(c).slice(0, 120))}
            </Typography>
          ))}
        </Paper>
      )}

      {recommendations.map((r, i) => (
        <Accordion key={i} disableGutters sx={{ mb: 1, bgcolor: 'background.paper' }}>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Typography sx={{ flex: 1 }}>
              {String(r.title ?? r.recommendation ?? `Recommendation ${i + 1}`)}
            </Typography>
            {r.priority != null && (
              <Chip label={String(r.priority)} size="small" variant="outlined" />
            )}
          </AccordionSummary>
          <AccordionDetails>
            <Typography variant="body2" color="text.secondary">
              {String(r.description ?? r.detail ?? r.text ?? '')}
            </Typography>
          </AccordionDetails>
        </Accordion>
      ))}

      {explanations.map((e, i) => (
        <Paper key={i} sx={{ p: 2, mb: 2 }}>
          <Typography variant="subtitle2" gutterBottom>
            AI Explanation — {String(e.pattern_id ?? e.failure_type ?? `#${i + 1}`)}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {String(e.explanation ?? e.text ?? e.summary ?? '')}
          </Typography>
          {Array.isArray(e.supporting_evidence) && e.supporting_evidence.length > 0 && (
            <Box sx={{ mt: 1 }}>
              <Typography variant="caption" color="text.secondary">
                Supporting Evidence:
              </Typography>
              {(e.supporting_evidence as string[]).map((ev, j) => (
                <Typography key={j} variant="body2" sx={{ pl: 2 }}>
                  • {ev}
                </Typography>
              ))}
            </Box>
          )}
        </Paper>
      ))}
    </>
  )
}
