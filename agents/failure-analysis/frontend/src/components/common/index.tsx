import { Box, Chip, Typography } from '@mui/material'
import type { ValidationStatus } from '../../types/evaluation'
import { statusColors } from '../../theme/darkTheme'

export function StatusChip({ status }: { status: ValidationStatus | string }) {
  const color = statusColors[status as ValidationStatus] ?? '#64748b'
  return (
    <Chip
      label={status}
      size="small"
      sx={{
        bgcolor: `${color}22`,
        color,
        border: `1px solid ${color}44`,
        fontWeight: 600,
        fontSize: '0.7rem',
      }}
    />
  )
}

export function PriorityChip({ priority }: { priority: string }) {
  const color =
    priority === 'High' ? '#ef5350' : priority === 'Medium' ? '#ffb74d' : '#4fc3f7'
  return (
    <Chip
      label={priority}
      size="small"
      sx={{ bgcolor: `${color}22`, color, fontWeight: 600, fontSize: '0.7rem' }}
    />
  )
}

export function PageHeader({
  title,
  subtitle,
  action,
}: {
  title: string
  subtitle?: string
  action?: React.ReactNode
}) {
  return (
    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 3 }}>
      <Box>
        <Typography variant="h4" gutterBottom>
          {title}
        </Typography>
        {subtitle && (
          <Typography variant="body2" color="text.secondary">
            {subtitle}
          </Typography>
        )}
      </Box>
      {action}
    </Box>
  )
}

export function StatCard({
  label,
  value,
  unit,
  accent,
}: {
  label: string
  value: string | number
  unit?: string
  accent?: string
}) {
  return (
    <Box
      sx={{
        p: 2,
        borderRadius: 2,
        border: '1px solid rgba(255,255,255,0.06)',
        bgcolor: 'background.paper',
        borderLeft: accent ? `3px solid ${accent}` : undefined,
      }}
    >
      <Typography variant="subtitle2" color="text.secondary">
        {label}
      </Typography>
      <Typography variant="h5" sx={{ mt: 0.5, fontWeight: 700 }}>
        {value}
        {unit && (
          <Typography component="span" variant="body2" color="text.secondary" sx={{ ml: 0.5 }}>
            {unit}
          </Typography>
        )}
      </Typography>
    </Box>
  )
}

export function MetricGauge({
  score,
  rating,
  size = 120,
}: {
  score: number
  rating: string
  size?: number
}) {
  const color =
    score >= 90 ? '#66bb6a' : score >= 75 ? '#4fc3f7' : score >= 55 ? '#ffb74d' : '#ef5350'
  return (
    <Box sx={{ textAlign: 'center' }}>
      <Box
        sx={{
          width: size,
          height: size,
          borderRadius: '50%',
          border: `4px solid ${color}`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          mx: 'auto',
          bgcolor: `${color}11`,
        }}
      >
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 700, color }}>
            {Math.round(score)}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            /100
          </Typography>
        </Box>
      </Box>
      <Typography variant="body2" sx={{ mt: 1, color, fontWeight: 600 }}>
        {rating}
      </Typography>
    </Box>
  )
}

export function EmptyState({ message }: { message: string }) {
  return (
    <Box
      sx={{
        py: 6,
        textAlign: 'center',
        color: 'text.secondary',
        border: '1px dashed rgba(255,255,255,0.1)',
        borderRadius: 2,
      }}
    >
      <Typography>{message}</Typography>
    </Box>
  )
}
