import { Alert, Paper, Typography } from '@mui/material'
import type { UploadResponse } from '../api/client'

interface Props {
  result?: UploadResponse | null
}

export default function ValidationReport({ result }: Props) {
  if (!result) {
    return (
      <Paper sx={{ p: 3, mt: 3 }}>
        <Typography variant="body2" color="text.secondary">
          Upload a file to view validation and processing statistics.
        </Typography>
      </Paper>
    )
  }

  const report = result.validation_report ?? result.upload.validation_report
  const stats = result.processing_statistics ?? result.upload.processing_statistics

  return (
    <Paper sx={{ p: 3, mt: 3 }}>
      <Typography variant="h6" gutterBottom>
        Validation Report
      </Typography>
      {result.duplicate && <Alert severity="warning">Duplicate upload detected.</Alert>}
      {result.upload.error_message && <Alert severity="error">{result.upload.error_message}</Alert>}
      <Typography variant="subtitle2" sx={{ mt: 2 }}>
        Processing Statistics
      </Typography>
      <pre style={{ overflow: 'auto', fontSize: 12 }}>{JSON.stringify(stats, null, 2)}</pre>
      <Typography variant="subtitle2" sx={{ mt: 2 }}>
        Validation Details
      </Typography>
      <pre style={{ overflow: 'auto', fontSize: 12 }}>{JSON.stringify(report, null, 2)}</pre>
      <Typography variant="subtitle2" sx={{ mt: 2 }}>
        Parsed Dataset Preview ({result.parsed_dataset_preview?.length ?? 0} rows)
      </Typography>
      <pre style={{ overflow: 'auto', fontSize: 12 }}>
        {JSON.stringify(result.parsed_dataset_preview?.slice(0, 5) ?? [], null, 2)}
      </pre>
    </Paper>
  )
}
