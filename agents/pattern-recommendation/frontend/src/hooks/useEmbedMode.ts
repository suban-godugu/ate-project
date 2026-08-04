import { useLocation } from 'react-router-dom'

/** True when the UI is hosted inside the VERILUMEN dashboard iframe. */
export function useEmbedMode(): boolean {
  const { search } = useLocation()
  return new URLSearchParams(search).get('embed') === '1'
}

/** Keep ?embed=1 on internal links so chrome stays hidden in the iframe. */
export function withEmbedParam(to: string, embed: boolean): string {
  if (!embed) return to
  const [path, qs = ''] = to.split('?')
  const params = new URLSearchParams(qs)
  params.set('embed', '1')
  return `${path}?${params.toString()}`
}
