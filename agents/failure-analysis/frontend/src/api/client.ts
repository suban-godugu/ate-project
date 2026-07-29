import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 600000,
})

export interface UploadSummary {
  id: string
  original_filename: string
  status: string
  parser_id?: string | null
  records_accepted?: number
  records_quarantined?: number
  integrity_pct?: number
  created_at?: string | null
}

export interface UploadResponse {
  duplicate?: boolean
  upload: UploadSummary & {
    file_size_bytes?: number
    checksum_sha256?: string
    validation_report?: Record<string, unknown>
    processing_statistics?: Record<string, unknown>
    error_message?: string | null
    completed_at?: string | null
  }
  parsed_dataset_preview?: Record<string, unknown>[]
  validation_report?: Record<string, unknown>
  processing_statistics?: Record<string, unknown>
  metadata?: Record<string, unknown>
}

export async function uploadFile(file: File, allowDuplicate = false): Promise<UploadResponse> {
  const form = new FormData()
  form.append('file', file)
  const { data } = await api.post<UploadResponse>(
    `/uploads?allow_duplicate=${allowDuplicate}`,
    form,
    { headers: { 'Content-Type': 'multipart/form-data' } },
  )
  return data
}

export async function listUploads(): Promise<{ uploads: UploadSummary[] }> {
  const { data } = await api.get<{ uploads: UploadSummary[] }>('/uploads')
  return data
}

export async function getUpload(id: string): Promise<{ upload: UploadResponse['upload'] }> {
  const { data } = await api.get(`/uploads/${id}`)
  return data
}

export async function getUploadMetadata(id: string): Promise<{ metadata: Record<string, unknown> }> {
  const { data } = await api.get(`/uploads/${id}/metadata`)
  return data
}

export async function deleteUpload(id: string): Promise<void> {
  await api.delete(`/uploads/${id}`)
}

export default api
