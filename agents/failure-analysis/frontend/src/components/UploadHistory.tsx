import {
  Chip,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material'
import { useQuery } from '@tanstack/react-query'
import { listUploads, type UploadSummary } from '../api/client'

interface Props {
  selectedId?: string
  onSelect: (upload: UploadSummary) => void
}

export default function UploadHistory({ selectedId, onSelect }: Props) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['uploads'],
    queryFn: listUploads,
    refetchInterval: 5000,
  })

  return (
    <Paper sx={{ p: 3, mt: 3 }}>
      <Typography variant="h6" gutterBottom>
        Upload History
      </Typography>
      {isLoading && <Typography>Loading...</Typography>}
      {error && <Typography color="error">{(error as Error).message}</Typography>}
      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell>File</TableCell>
            <TableCell>Status</TableCell>
            <TableCell>Parser</TableCell>
            <TableCell align="right">Accepted</TableCell>
            <TableCell align="right">Integrity</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {(data?.uploads ?? []).map((row) => (
            <TableRow
              key={row.id}
              hover
              selected={row.id === selectedId}
              sx={{ cursor: 'pointer' }}
              onClick={() => onSelect(row)}
            >
              <TableCell>{row.original_filename}</TableCell>
              <TableCell>
                <Chip size="small" label={row.status} color={row.status === 'completed' ? 'success' : 'default'} />
              </TableCell>
              <TableCell>{row.parser_id ?? '-'}</TableCell>
              <TableCell align="right">{row.records_accepted ?? 0}</TableCell>
              <TableCell align="right">{row.integrity_pct?.toFixed?.(1) ?? '-'}%</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </Paper>
  )
}
