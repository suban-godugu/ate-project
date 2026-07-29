import {
  Paper,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
  LinearProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from '@mui/material'
import ExpandMoreIcon from '@mui/icons-material/ExpandMore'
import { useQuery } from '@tanstack/react-query'
import { getEvaluationReport } from '../api/evaluationApi'
import { PageHeader, StatusChip, EmptyState } from '../components/common'
import { useWorkbench } from '../context/WorkbenchContext'
import { FA_MODULES, MODULE_LABELS } from '../types/evaluation'

export default function FunctionalValidation() {
  const { executionId } = useWorkbench()
  const { data, isLoading } = useQuery({
    queryKey: ['evaluation-report', executionId],
    queryFn: () => getEvaluationReport(executionId ?? undefined),
    enabled: true,
  })

  if (isLoading) return <LinearProgress />

  const results = data?.report?.dataset_results ?? []
  const allValidation = results.flatMap((d) =>
    d.validation.map((v) => ({ ...v, dataset_id: d.dataset?.dataset_id })),
  )

  const byModule = FA_MODULES.map((mod) => {
    const row = allValidation.find((v) => v.module === mod)
    return { module: mod, ...row }
  })

  return (
    <>
      <PageHeader
        title="Functional Validation"
        subtitle="FA-FR-001 through FA-FR-010 requirement verification"
      />

      {allValidation.length === 0 ? (
        <EmptyState message="No validation results. Run an evaluation from Run Analysis." />
      ) : (
        <>
          <Paper sx={{ mb: 3, overflow: 'auto' }}>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Module</TableCell>
                  <TableCell>Requirement</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Duration</TableCell>
                  <TableCell>Result</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {byModule.map(({ module, status, duration_ms, explanation }) => (
                  <TableRow key={module}>
                    <TableCell>
                      <Typography variant="body2" fontWeight={600}>
                        {module}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="caption">{MODULE_LABELS[module]}</Typography>
                    </TableCell>
                    <TableCell>
                      {status ? <StatusChip status={status} /> : <StatusChip status="SKIPPED" />}
                    </TableCell>
                    <TableCell>{duration_ms ? `${duration_ms.toFixed(0)} ms` : '—'}</TableCell>
                    <TableCell>
                      <Typography variant="body2" color="text.secondary">
                        {explanation ?? 'Not executed'}
                      </Typography>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </Paper>

          {byModule
            .filter((r) => r.explanation)
            .map(({ module, status, explanation }) => (
              <Accordion key={module} disableGutters sx={{ mb: 1, bgcolor: 'background.paper' }}>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Typography sx={{ flex: 1 }}>{module}</Typography>
                  {status && <StatusChip status={status} />}
                </AccordionSummary>
                <AccordionDetails>
                  <Typography variant="body2" color="text.secondary">
                    {explanation}
                  </Typography>
                </AccordionDetails>
              </Accordion>
            ))}
        </>
      )}
    </>
  )
}
