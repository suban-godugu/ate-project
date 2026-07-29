import {
  Box,
  Button,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  Paper,
  Typography,
  LinearProgress,
  Checkbox,
  ListItemText,
  OutlinedInput,
  Grid,
  Alert,
} from '@mui/material'
import PlayArrowIcon from '@mui/icons-material/PlayArrow'
import StopIcon from '@mui/icons-material/Stop'
import { useMutation, useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { discoverDatasets, runEvaluation } from '../api/evaluationApi'
import { PageHeader, StatusChip } from '../components/common'
import { useWorkbench } from '../context/WorkbenchContext'
import { FA_MODULES, MODULE_LABELS } from '../types/evaluation'

export default function ExecutionPanel() {
  const { selectedDatasetId, setSelectedDatasetId, setExecutionId, setLastRun, isRunning, setIsRunning } =
    useWorkbench()
  const [mode, setMode] = useState<'full' | 'partial'>('full')
  const [modules, setModules] = useState<string[]>([...FA_MODULES])
  const [maxLogs, setMaxLogs] = useState(30)
  const [progress, setProgress] = useState<string[]>([])

  const { data: inventory } = useQuery({ queryKey: ['datasets'], queryFn: discoverDatasets })

  const mutation = useMutation({
    mutationFn: runEvaluation,
    onMutate: () => {
      setIsRunning(true)
      setProgress(['Starting evaluation pipeline…'])
    },
    onSuccess: (result) => {
      setExecutionId(result.execution_id)
      setLastRun(result)
      const logs = result.dataset_results.flatMap((d) =>
        d.validation.map((v) => `${v.module}: ${v.status}`),
      )
      setProgress(logs.length ? logs : ['Completed'])
      setIsRunning(false)
    },
    onError: (err: Error) => {
      setProgress([`Error: ${err.message}`])
      setIsRunning(false)
    },
  })

  const bundles = inventory?.bundles?.filter((b) => b.scale_token !== 'unmatched') ?? []

  return (
    <>
      <PageHeader
        title="Run Analysis"
        subtitle="Execute complete or per-module FA-FR validation pipeline"
      />

      <Grid container spacing={3}>
        <Grid item xs={12} md={5}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              Configuration
            </Typography>
            <FormControl fullWidth size="small" sx={{ mt: 2 }}>
              <InputLabel>Dataset</InputLabel>
              <Select
                value={selectedDatasetId ?? ''}
                label="Dataset"
                onChange={(e) => setSelectedDatasetId(e.target.value || null)}
              >
                {bundles.map((b) => (
                  <MenuItem key={b.dataset_id} value={b.dataset_id}>
                    {b.dataset_id} ({b.scale_token} — {b.log_count} logs)
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <FormControl fullWidth size="small" sx={{ mt: 2 }}>
              <InputLabel>Execution Mode</InputLabel>
              <Select
                value={mode}
                label="Execution Mode"
                onChange={(e) => setMode(e.target.value as 'full' | 'partial')}
              >
                <MenuItem value="full">Complete Pipeline (FA-FR-001..010)</MenuItem>
                <MenuItem value="partial">Individual Modules</MenuItem>
              </Select>
            </FormControl>

            {mode === 'partial' && (
              <FormControl fullWidth size="small" sx={{ mt: 2 }}>
                <InputLabel>Modules</InputLabel>
                <Select
                  multiple
                  value={modules}
                  onChange={(e) => setModules(e.target.value as string[])}
                  input={<OutlinedInput label="Modules" />}
                  renderValue={(sel) => sel.join(', ')}
                >
                  {FA_MODULES.map((m) => (
                    <MenuItem key={m} value={m}>
                      <Checkbox checked={modules.includes(m)} />
                      <ListItemText primary={`${m} — ${MODULE_LABELS[m]}`} />
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            )}

            <FormControl fullWidth size="small" sx={{ mt: 2 }}>
              <InputLabel>Max Logs</InputLabel>
              <Select value={maxLogs} label="Max Logs" onChange={(e) => setMaxLogs(Number(e.target.value))}>
                {[10, 20, 30, 50, 100, 200].map((n) => (
                  <MenuItem key={n} value={n}>
                    {n}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <Box sx={{ mt: 3, display: 'flex', gap: 1 }}>
              <Button
                variant="contained"
                startIcon={<PlayArrowIcon />}
                disabled={isRunning || !selectedDatasetId}
                onClick={() =>
                  mutation.mutate({
                    dataset_id: selectedDatasetId,
                    modules: mode === 'full' ? null : modules,
                    max_logs: maxLogs,
                  })
                }
              >
                Run Evaluation
              </Button>
              <Button
                variant="outlined"
                color="error"
                startIcon={<StopIcon />}
                disabled={!isRunning}
                onClick={() => setIsRunning(false)}
              >
                Cancel
              </Button>
            </Box>
          </Paper>
        </Grid>

        <Grid item xs={12} md={7}>
          <Paper sx={{ p: 2, minHeight: 360 }}>
            <Typography variant="subtitle2" gutterBottom>
              Execution Progress
            </Typography>
            {isRunning && <LinearProgress sx={{ mb: 2 }} />}
            {mutation.data && (
              <Alert severity="success" sx={{ mb: 2 }}>
                Completed in {(mutation.data.processing_ms / 1000).toFixed(1)}s — Execution ID:{' '}
                {mutation.data.execution_id.slice(0, 12)}…
              </Alert>
            )}
            <Box sx={{ maxHeight: 300, overflow: 'auto', fontFamily: 'monospace', fontSize: 13 }}>
              {progress.map((line, i) => (
                <Box key={i} sx={{ py: 0.5, display: 'flex', alignItems: 'center', gap: 1 }}>
                  {line.includes(':') && (
                    <StatusChip status={line.split(': ')[1] as 'PASS' | 'FAIL' | 'WARNING'} />
                  )}
                  <span>{line}</span>
                </Box>
              ))}
            </Box>
          </Paper>
        </Grid>
      </Grid>
    </>
  )
}
