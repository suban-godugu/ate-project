import { Alert, Box, Button, LinearProgress, Paper, Typography } from '@mui/material'
import { useMutation } from '@tanstack/react-query'
import { useState } from 'react'
import { uploadFile, type UploadResponse } from '../api/client'

interface Props {
  onUploaded: (result: UploadResponse) => void
}

export default function UploadComponent({ onUploaded }: Props) {
  const [file, setFile] = useState<File | null>(null)
  const mutation = useMutation({
    mutationFn: (selected: File) => uploadFile(selected),
    onSuccess: (data) => onUploaded(data),
  })

  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom>
        Upload Test File
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        STDF, ASCII tester logs, CSV, XML, JSON, and YAML-configured custom templates.
      </Typography>
      <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
        <Button variant="outlined" component="label">
          Choose File
          <input
            hidden
            type="file"
            accept=".stdf,.std,.log,.txt,.dat,.csv,.xml,.json"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          />
        </Button>
        <Typography variant="body2">{file?.name ?? 'No file selected'}</Typography>
        <Button
          variant="contained"
          disabled={!file || mutation.isPending}
          onClick={() => file && mutation.mutate(file)}
        >
          Upload &amp; Ingest
        </Button>
      </Box>
      {mutation.isPending && <LinearProgress sx={{ mt: 2 }} />}
      {mutation.isError && (
        <Alert severity="error" sx={{ mt: 2 }}>
          {(mutation.error as Error).message}
        </Alert>
      )}
    </Paper>
  )
}
