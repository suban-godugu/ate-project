import {
  Box,
  Button,
  Grid,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
  Alert,
  IconButton,
  Tooltip,
  LinearProgress,
} from '@mui/material'
import RefreshIcon from '@mui/icons-material/Refresh'
import ArrowForwardIcon from '@mui/icons-material/ArrowForward'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { discoverDatasets } from '../api/evaluationApi'
import { PageHeader, StatusChip } from '../components/common'
import { useWorkbench } from '../context/WorkbenchContext'

export default function DatasetManager() {
  const qc = useQueryClient()
  const { setSelectedDatasetId } = useWorkbench()
  const { data, isLoading, isFetching, refetch } = useQuery({
    queryKey: ['datasets'],
    queryFn: discoverDatasets,
  })

  if (isLoading) return <LinearProgress />

  return (
    <>
      <PageHeader
        title="Dataset Manager"
        subtitle="Auto-discovered STIL files and tester log corpora with scale matching"
        action={
          <Button startIcon={<RefreshIcon />} onClick={() => refetch()} disabled={isFetching}>
            Refresh
          </Button>
        }
      />

      {(data?.warnings ?? []).slice(0, 3).map((w) => (
        <Alert key={w} severity="warning" sx={{ mb: 1 }}>
          {w}
        </Alert>
      ))}

      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={4}>
          <Paper sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant="h4">{data?.stil_count ?? 0}</Typography>
            <Typography variant="caption" color="text.secondary">
              STIL Files
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={4}>
          <Paper sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant="h4">{data?.log_count ?? 0}</Typography>
            <Typography variant="caption" color="text.secondary">
              Tester Logs
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={4}>
          <Paper sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant="h4">{data?.bundles?.length ?? 0}</Typography>
            <Typography variant="caption" color="text.secondary">
              Matched Bundles
            </Typography>
          </Paper>
        </Grid>
      </Grid>

      <Paper sx={{ overflow: 'auto' }}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Dataset</TableCell>
              <TableCell>Scale</TableCell>
              <TableCell>STIL</TableCell>
              <TableCell>Logs</TableCell>
              <TableCell>Labelled</TableCell>
              <TableCell>Match Status</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {(data?.bundles ?? []).map((b) => (
              <TableRow key={b.dataset_id} hover>
                <TableCell>
                  <Typography variant="body2" fontWeight={600}>
                    {b.dataset_id}
                  </Typography>
                </TableCell>
                <TableCell>{b.scale_token}</TableCell>
                <TableCell>{b.stil_paths.length}</TableCell>
                <TableCell>{b.log_count}</TableCell>
                <TableCell>{b.labelled_log_count}</TableCell>
                <TableCell>
                  {b.warnings.length ? (
                    <StatusChip status="WARNING" />
                  ) : b.stil_paths.length && b.log_count ? (
                    <StatusChip status="PASS" />
                  ) : (
                    <StatusChip status="SKIPPED" />
                  )}
                </TableCell>
                <TableCell align="right">
                  <Tooltip title="Select for evaluation">
                    <IconButton
                      size="small"
                      color="primary"
                      onClick={() => {
                        setSelectedDatasetId(b.scale_token === 'unmatched' ? b.dataset_id : b.scale_token)
                        qc.invalidateQueries({ queryKey: ['workbench-overview'] })
                      }}
                    >
                      <ArrowForwardIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Paper>

      {data?.stil_files && data.stil_files.length > 0 && (
        <Box sx={{ mt: 3 }}>
          <Typography variant="subtitle2" gutterBottom>
            Discovered STIL Files
          </Typography>
          <Paper sx={{ p: 2, maxHeight: 200, overflow: 'auto' }}>
            {data.stil_files.map((f) => (
              <Typography key={f} variant="caption" display="block" sx={{ fontFamily: 'monospace', py: 0.25 }}>
                {f}
              </Typography>
            ))}
          </Paper>
        </Box>
      )}
    </>
  )
}
