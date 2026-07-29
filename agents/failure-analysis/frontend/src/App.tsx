import { CssBaseline, ThemeProvider } from '@mui/material'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { darkTheme } from './theme/darkTheme'
import { WorkbenchProvider } from './context/WorkbenchContext'
import AppShell from './layout/AppShell'
import LandingDashboard from './pages/LandingDashboard'
import DatasetManager from './pages/DatasetManager'
import ExecutionPanel from './pages/ExecutionPanel'
import FunctionalValidation from './pages/FunctionalValidation'
import AIEvaluation from './pages/AIEvaluation'
import PerformanceDashboard from './pages/PerformanceDashboard'
import Visualizations from './pages/Visualizations'
import RootCauseScreen from './pages/RootCauseScreen'
import ReportsScreen from './pages/ReportsScreen'
import ImprovementCenter from './pages/ImprovementCenter'
import BenchmarkScreen from './pages/BenchmarkScreen'
import TrainingScreen from './pages/TrainingScreen'
import LogViewer from './pages/LogViewer'
import UploadPage from './pages/UploadPage'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: 1,
    },
  },
})

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={darkTheme}>
        <CssBaseline />
        <BrowserRouter>
          <WorkbenchProvider>
            <Routes>
              <Route element={<AppShell />}>
                <Route index element={<LandingDashboard />} />
                <Route path="datasets" element={<DatasetManager />} />
                <Route path="execute" element={<ExecutionPanel />} />
                <Route path="validation" element={<FunctionalValidation />} />
                <Route path="ai-evaluation" element={<AIEvaluation />} />
                <Route path="performance" element={<PerformanceDashboard />} />
                <Route path="visualizations" element={<Visualizations />} />
                <Route path="root-cause" element={<RootCauseScreen />} />
                <Route path="reports" element={<ReportsScreen />} />
                <Route path="improvements" element={<ImprovementCenter />} />
                <Route path="benchmark" element={<BenchmarkScreen />} />
                <Route path="training" element={<TrainingScreen />} />
                <Route path="logs" element={<LogViewer />} />
                <Route path="upload" element={<UploadPage />} />
              </Route>
            </Routes>
          </WorkbenchProvider>
        </BrowserRouter>
      </ThemeProvider>
    </QueryClientProvider>
  )
}
