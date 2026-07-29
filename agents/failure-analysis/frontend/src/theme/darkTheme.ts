import { createTheme } from '@mui/material/styles'

export const darkTheme = createTheme({
  palette: {
    mode: 'dark',
    primary: { main: '#4fc3f7', light: '#8bf6ff', dark: '#0093c4' },
    secondary: { main: '#81c784' },
    error: { main: '#ef5350' },
    warning: { main: '#ffb74d' },
    success: { main: '#66bb6a' },
    background: {
      default: '#0a0e17',
      paper: '#111827',
    },
    divider: 'rgba(255,255,255,0.08)',
    text: {
      primary: '#e8edf5',
      secondary: '#94a3b8',
    },
  },
  typography: {
    fontFamily: '"IBM Plex Sans", "Segoe UI", Roboto, sans-serif',
    h4: { fontWeight: 600, letterSpacing: '-0.02em' },
    h5: { fontWeight: 600 },
    h6: { fontWeight: 600 },
    subtitle2: { fontWeight: 500, letterSpacing: '0.04em', textTransform: 'uppercase', fontSize: '0.7rem' },
  },
  shape: { borderRadius: 8 },
  components: {
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
          border: '1px solid rgba(255,255,255,0.06)',
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
          border: '1px solid rgba(255,255,255,0.06)',
        },
      },
    },
    MuiDrawer: {
      styleOverrides: {
        paper: {
          backgroundColor: '#0d1320',
          borderRight: '1px solid rgba(255,255,255,0.06)',
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundColor: '#0d1320',
          borderBottom: '1px solid rgba(255,255,255,0.06)',
          boxShadow: 'none',
        },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        head: { fontWeight: 600, color: '#94a3b8', fontSize: '0.75rem', textTransform: 'uppercase' },
      },
    },
  },
})

export const statusColors = {
  PASS: '#66bb6a',
  FAIL: '#ef5350',
  WARNING: '#ffb74d',
  SKIPPED: '#64748b',
} as const
