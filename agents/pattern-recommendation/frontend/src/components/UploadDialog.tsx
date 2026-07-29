import { Modal } from './Modal'

interface UploadDialogProps {
  open: boolean
  onClose: () => void
  onRefresh: () => void
  refreshing: boolean
}

export function UploadDialog({
  open,
  onClose,
  onRefresh,
  refreshing,
}: UploadDialogProps) {
  return (
    <Modal
      open={open}
      title="Load / refresh data"
      onClose={onClose}
      footer={
        <>
          <button
            type="button"
            onClick={onClose}
            className="rounded-xl border border-white/10 px-4 py-2 text-sm text-ink-200 hover:bg-white/5"
          >
            Close
          </button>
          <button
            type="button"
            disabled={refreshing}
            onClick={onRefresh}
            className="rounded-xl bg-accent-600 px-4 py-2 text-sm font-medium text-white hover:bg-accent-700 disabled:opacity-60"
          >
            {refreshing ? 'Refreshing…' : 'Refresh All'}
          </button>
        </>
      }
    >
      <p>
        The FastAPI backend loads datasets from the project <code className="text-accent-400">data/</code> and{' '}
        <code className="text-accent-400">outputs/</code> folders. There is no upload endpoint — place logs and
        analysis files on disk, then refresh caches.
      </p>
      <ul className="mt-3 list-disc space-y-1 pl-5 text-ink-300">
        <li>ATE logs → run failure aggregation agent</li>
        <li>
          Then call existing <code className="text-accent-400">POST /failures/refresh</code> and{' '}
          <code className="text-accent-400">POST /recommendations/refresh</code>
        </li>
      </ul>
    </Modal>
  )
}
