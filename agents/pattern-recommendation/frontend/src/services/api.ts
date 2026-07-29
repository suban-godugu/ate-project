import axios, { type AxiosError } from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? '',
  timeout: 180_000,
  headers: { 'Content-Type': 'application/json' },
})

export function getErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const ax = error as AxiosError<{ message?: string; detail?: string }>
    const data = ax.response?.data
    if (data && typeof data === 'object') {
      if (data.message) return data.message
      if (data.detail) return String(data.detail)
    }
    if (ax.message) return ax.message
  }
  if (error instanceof Error) return error.message
  return 'Unexpected error'
}

export default api
