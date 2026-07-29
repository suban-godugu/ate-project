import { Box } from '@mui/material'
import { useState } from 'react'
import type { UploadResponse, UploadSummary } from '../api/client'
import UploadComponent from '../components/UploadComponent'
import UploadHistory from '../components/UploadHistory'
import ValidationReport from '../components/ValidationReport'
import { PageHeader } from '../components/common'

export default function UploadPage() {
  const [latest, setLatest] = useState<UploadResponse | null>(null)
  const [selected, setSelected] = useState<UploadSummary | undefined>()

  return (
    <Box>
      <PageHeader
        title="FA-FR-001 Data Ingestion"
        subtitle="Enterprise ingestion for STDF, ASCII tester logs, CSV, XML, JSON, and custom templates"
      />
      <UploadComponent
        onUploaded={(result) => {
          setLatest(result)
          setSelected(result.upload)
        }}
      />
      <ValidationReport result={latest} />
      <UploadHistory selectedId={selected?.id} onSelect={setSelected} />
    </Box>
  )
}
