import {
  Grid,
  Paper,
  Typography,
  LinearProgress,
  Alert,
  List,
  ListItem,
  ListItemText,
  Divider,
} from '@mui/material'
import { useQuery } from '@tanstack/react-query'
import { getImprovements } from '../api/evaluationApi'
import { PageHeader, MetricGauge, PriorityChip, EmptyState } from '../components/common'
import { useWorkbench } from '../context/WorkbenchContext'

export default function ImprovementCenter() {
  const { executionId } = useWorkbench()
  const { data, isLoading, isError } = useQuery({
    queryKey: ['improvements', executionId],
    queryFn: () => getImprovements(executionId ?? undefined),
  })

  if (isLoading) return <LinearProgress />

  if (isError || !data) {
    return (
      <>
        <PageHeader title="Agent Improvement Center" subtitle="Automated analysis and optimization recommendations" />
        <EmptyState message="No evaluation data for improvement analysis. Run an evaluation first." />
      </>
    )
  }

  const recs = data.recommendations ?? []
  const readiness = data.production_readiness
  const health = data.ai_health_score

  const byPriority = {
    High: recs.filter((r) => r.priority === 'High'),
    Medium: recs.filter((r) => r.priority === 'Medium'),
    Low: recs.filter((r) => r.priority === 'Low'),
  }

  return (
    <>
      <PageHeader
        title="Agent Improvement Center"
        subtitle="Architecture, performance, accuracy, and prompt engineering recommendations"
      />

      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} md={3}>
          <Paper sx={{ p: 3, display: 'flex', justifyContent: 'center' }}>
            <MetricGauge score={health.score} rating={health.rating} size={130} />
          </Paper>
        </Grid>
        <Grid item xs={12} md={9}>
          <Alert
            severity={readiness.production_ready ? 'success' : 'warning'}
            sx={{ mb: 2 }}
          >
            {readiness.production_ready
              ? 'Agent meets production readiness criteria.'
              : `Not production-ready: ${readiness.blockers.join('; ')}`}
          </Alert>
          <Grid container spacing={2}>
            <Grid item xs={4}>
              <Paper sx={{ p: 2, textAlign: 'center' }}>
                <Typography variant="h4" color="success.main">
                  {readiness.pass_count}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  PASS
                </Typography>
              </Paper>
            </Grid>
            <Grid item xs={4}>
              <Paper sx={{ p: 2, textAlign: 'center' }}>
                <Typography variant="h4" color="warning.main">
                  {readiness.warning_count}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  WARNING
                </Typography>
              </Paper>
            </Grid>
            <Grid item xs={4}>
              <Paper sx={{ p: 2, textAlign: 'center' }}>
                <Typography variant="h4" color="error.main">
                  {readiness.fail_count}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  FAIL
                </Typography>
              </Paper>
            </Grid>
          </Grid>
        </Grid>
      </Grid>

      {(['High', 'Medium', 'Low'] as const).map((priority) => {
        const items = byPriority[priority]
        if (items.length === 0) return null
        return (
          <Paper key={priority} sx={{ mb: 3, p: 2 }}>
            <Typography variant="subtitle2" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <PriorityChip priority={priority} /> {priority} Priority ({items.length})
            </Typography>
            <List dense disablePadding>
              {items.map((r, i) => (
                <div key={i}>
                  {i > 0 && <Divider sx={{ my: 1 }} />}
                  <ListItem disableGutters alignItems="flex-start">
                    <ListItemText
                      primary={
                        <Typography variant="body2" fontWeight={600}>
                          [{r.category}] {r.module} — {r.recommendation}
                        </Typography>
                      }
                      secondary={
                        <Typography variant="caption" color="text.secondary">
                          {r.rationale}
                          {r.dataset_id ? ` · Dataset: ${r.dataset_id}` : ''}
                        </Typography>
                      }
                    />
                  </ListItem>
                </div>
              ))}
            </List>
          </Paper>
        )
      })}

      {recs.length === 0 && (
        <EmptyState message="No improvement recommendations — agent performance is within thresholds." />
      )}
    </>
  )
}
