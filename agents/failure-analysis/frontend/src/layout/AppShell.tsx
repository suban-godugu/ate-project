import { AppBar, Box, Chip, Toolbar, Typography } from '@mui/material'
import { useQuery } from '@tanstack/react-query'
import { useEffect } from 'react'
import { Outlet } from 'react-router-dom'
import Sidebar, { DRAWER_WIDTH } from './Sidebar'
import { getWorkbenchOverview } from '../api/evaluationApi'
import { useWorkbench } from '../context/WorkbenchContext'

export default function AppShell() {
  const { isRunning, executionId, setExecutionId } = useWorkbench()
  const { data: overview } = useQuery({
    queryKey: ['workbench-overview'],
    queryFn: getWorkbenchOverview,
    refetchInterval: 15000,
  })

  useEffect(() => {
    const latest = overview?.latest_execution?.execution_id
    if (!executionId && latest) {
      setExecutionId(latest)
    }
  }, [overview?.latest_execution?.execution_id, executionId, setExecutionId])

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh', bgcolor: 'background.default' }}>
      <Sidebar />
      <Box component="main" sx={{ flexGrow: 1, width: `calc(100% - ${DRAWER_WIDTH}px)` }}>
        <AppBar position="sticky" elevation={0}>
          <Toolbar sx={{ justifyContent: 'space-between' }}>
            <Typography variant="body2" color="text.secondary">
              Failure Analysis Agent — Evaluation & Benchmarking Platform
            </Typography>
            <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
              {isRunning && (
                <Chip label="Running" size="small" color="primary" variant="outlined" />
              )}
              <Chip
                label={`Agent: ${overview?.agent_status ?? '—'}`}
                size="small"
                color={overview?.agent_status === 'ready' ? 'success' : 'warning'}
                variant="outlined"
              />
              <Chip
                label={`DB: ${overview?.database_health ?? '—'}`}
                size="small"
                variant="outlined"
              />
            </Box>
          </Toolbar>
        </AppBar>
        <Box sx={{ p: 3, maxWidth: 1600, mx: 'auto' }}>
          <Outlet />
        </Box>
      </Box>
    </Box>
  )
}
