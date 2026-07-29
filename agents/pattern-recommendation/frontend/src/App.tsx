import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { AppLayout } from '@/layouts/AppLayout'
import { OverviewPage } from '@/pages/OverviewPage'
import { FailuresPage } from '@/pages/FailuresPage'
import { DomainPage } from '@/pages/DomainPage'
import { SettingsPage } from '@/pages/SettingsPage'

export default function App() {
  return (
    <BrowserRouter basename={import.meta.env.BASE_URL}>
      <Routes>
        <Route element={<AppLayout />}>
          <Route index element={<OverviewPage />} />
          <Route path="failures" element={<FailuresPage />} />
          <Route path="removal" element={<DomainPage domain="removal" />} />
          <Route path="ordering" element={<DomainPage domain="ordering" />} />
          <Route
            path="redundancy"
            element={<DomainPage domain="redundancy" />}
          />
          <Route path="gap" element={<DomainPage domain="gap" />} />
          <Route path="low-power" element={<DomainPage domain="low_power" />} />
          <Route path="coverage" element={<DomainPage domain="coverage" />} />
          <Route path="settings" element={<SettingsPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
