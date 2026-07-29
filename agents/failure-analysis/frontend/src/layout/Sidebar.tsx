import {
  Drawer,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Toolbar,
  Typography,
  Box,
  Divider,
} from '@mui/material'
import { useLocation, useNavigate } from 'react-router-dom'
import DashboardIcon from '@mui/icons-material/Dashboard'
import StorageIcon from '@mui/icons-material/Storage'
import PlayCircleOutlineIcon from '@mui/icons-material/PlayCircleOutline'
import FactCheckIcon from '@mui/icons-material/FactCheck'
import PsychologyIcon from '@mui/icons-material/Psychology'
import SpeedIcon from '@mui/icons-material/Speed'
import BubbleChartIcon from '@mui/icons-material/BubbleChart'
import TroubleshootIcon from '@mui/icons-material/Troubleshoot'
import DescriptionIcon from '@mui/icons-material/Description'
import AutoFixHighIcon from '@mui/icons-material/AutoFixHigh'
import CompareArrowsIcon from '@mui/icons-material/CompareArrows'
import ModelTrainingIcon from '@mui/icons-material/ModelTraining'
import TerminalIcon from '@mui/icons-material/Terminal'
import CloudUploadIcon from '@mui/icons-material/CloudUpload'

const DRAWER_WIDTH = 260

const navItems = [
  { path: '/', label: 'Overview', icon: DashboardIcon },
  { path: '/datasets', label: 'Dataset Manager', icon: StorageIcon },
  { path: '/execute', label: 'Run Analysis', icon: PlayCircleOutlineIcon },
  { path: '/validation', label: 'Functional Validation', icon: FactCheckIcon },
  { path: '/ai-evaluation', label: 'AI Evaluation', icon: PsychologyIcon },
  { path: '/performance', label: 'Performance', icon: SpeedIcon },
  { path: '/visualizations', label: 'Visualizations', icon: BubbleChartIcon },
  { path: '/root-cause', label: 'Root Cause', icon: TroubleshootIcon },
  { path: '/reports', label: 'Reports', icon: DescriptionIcon },
  { path: '/improvements', label: 'Improvement Center', icon: AutoFixHighIcon },
  { path: '/benchmark', label: 'Benchmark', icon: CompareArrowsIcon },
  { path: '/training', label: 'AI Training', icon: ModelTrainingIcon },
  { path: '/logs', label: 'Live Logs', icon: TerminalIcon },
  { path: '/upload', label: 'File Upload', icon: CloudUploadIcon },
]

export default function Sidebar() {
  const navigate = useNavigate()
  const location = useLocation()

  return (
    <Drawer
      variant="permanent"
      sx={{
        width: DRAWER_WIDTH,
        flexShrink: 0,
        '& .MuiDrawer-paper': { width: DRAWER_WIDTH, boxSizing: 'border-box' },
      }}
    >
      <Toolbar>
        <Box>
          <Typography variant="subtitle2" color="primary" sx={{ letterSpacing: 2 }}>
            VERILUMEN
          </Typography>
          <Typography variant="caption" color="text.secondary">
            AI Evaluation Workbench
          </Typography>
        </Box>
      </Toolbar>
      <Divider />
      <List dense sx={{ px: 1, py: 1 }}>
        {navItems.map(({ path, label, icon: Icon }) => (
          <ListItemButton
            key={path}
            selected={location.pathname === path}
            onClick={() => navigate(path)}
            sx={{
              borderRadius: 1,
              mb: 0.25,
              '&.Mui-selected': {
                bgcolor: 'rgba(79, 195, 247, 0.12)',
                borderLeft: '2px solid',
                borderColor: 'primary.main',
              },
            }}
          >
            <ListItemIcon sx={{ minWidth: 36, color: 'primary.main' }}>
              <Icon fontSize="small" />
            </ListItemIcon>
            <ListItemText
              primary={label}
              primaryTypographyProps={{ fontSize: '0.85rem', fontWeight: 500 }}
            />
          </ListItemButton>
        ))}
      </List>
    </Drawer>
  )
}

export { DRAWER_WIDTH }
