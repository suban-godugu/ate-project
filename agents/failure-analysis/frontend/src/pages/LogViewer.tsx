import {
  Paper,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
  LinearProgress,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Box,
} from '@mui/material'
import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { getWorkbenchLogs } from '../api/evaluationApi'
import { PageHeader, StatusChip, EmptyState } from '../components/common'
import { useWorkbench } from '../context/WorkbenchContext'
import { FA_MODULES } from '../types/evaluation'

export default function LogViewer() {
  const { executionId } = useWorkbench()
  const [moduleFilter, setModuleFilter] = useState('')
  const [statusFilter, setStatusFilter] = useState('')

  const { data, isLoading, isFetching } = useQuery({
    queryKey: ['workbench-logs', executionId, moduleFilter, statusFilter],
    queryFn: () =>
      getWorkbenchLogs(executionId ?? undefined, {
        module: moduleFilter || undefined,
        status: statusFilter || undefined,
      }),
    refetchInterval: 5000,
  })

  const logs = data?.logs ?? []

  return (
    <>
      <PageHeader
        title="Live Logs"
        subtitle="Execution logs with module, status, and timing filters"
        action={
          <Typography variant="caption" color="text.secondary">
            {isFetching ? 'Refreshing…' : `${data?.total ?? 0} entries`}
          </Typography>
        }
      />

      <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
        <FormControl size="small" sx={{ minWidth: 160 }}>
          <InputLabel>Module</InputLabel>
          <Select
            value={moduleFilter}
            label="Module"
            onChange={(e) => setModuleFilter(e.target.value)}
          >
            <MenuItem value="">All</MenuItem>
            {FA_MODULES.map((m) => (
              <MenuItem key={m} value={m}>
                {m}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
        <FormControl size="small" sx={{ minWidth: 140 }}>
          <InputLabel>Status</InputLabel>
          <Select
            value={statusFilter}
            label="Status"
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <MenuItem value="">All</MenuItem>
            {['PASS', 'FAIL', 'WARNING', 'INFO', 'ERROR'].map((s) => (
              <MenuItem key={s} value={s}>
                {s}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
      </Box>

      {isLoading ? (
        <LinearProgress />
      ) : logs.length === 0 ? (
        <EmptyState message="No logs for current filters. Run an evaluation to populate logs." />
      ) : (
        <Paper sx={{ overflow: 'auto', maxHeight: '70vh' }}>
          <Table size="small" stickyHeader>
            <TableHead>
              <TableRow>
                <TableCell>Timestamp</TableCell>
                <TableCell>Module</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Duration</TableCell>
                <TableCell>Message</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {[...logs].reverse().map((log, i) => (
                <TableRow key={i} hover>
                  <TableCell sx={{ whiteSpace: 'nowrap', fontSize: '0.75rem' }}>
                    {log.timestamp}
                  </TableCell>
                  <TableCell>{log.module}</TableCell>
                  <TableCell>
                    <StatusChip status={log.status} />
                  </TableCell>
                  <TableCell>
                    {log.duration_ms != null ? `${log.duration_ms.toFixed(0)} ms` : '—'}
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" color="text.secondary" sx={{ maxWidth: 480 }}>
                      {log.message ?? log.exception ?? '—'}
                    </Typography>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Paper>
      )}
    </>
  )
}
