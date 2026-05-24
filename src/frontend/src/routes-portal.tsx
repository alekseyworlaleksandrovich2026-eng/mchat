/** Cloud-only portal routes (imported by AppPortal / main-portal only). */
import { lazy, Suspense } from 'react'
import { Routes, Route } from 'react-router-dom'
import { UserLayout } from './components/layout/UserLayout'
import { Spinner } from './components/ui/Spinner'

const lazyNamed = <T extends Record<string, React.ComponentType<any>>>(
  loader: () => Promise<T>,
  name: keyof T
) => lazy(() => loader().then(m => ({ default: m[name] })))

const RegisterPage = lazyNamed(() => import('./pages/RegisterPage'), 'RegisterPage')
const PortalDashboard = lazyNamed(() => import('./pages/portal/DashboardPage'), 'DashboardPage')
const PortalTemplates = lazyNamed(() => import('./pages/portal/TemplatesPage'), 'TemplatesPage')
const PortalTemplateDetail = lazyNamed(
  () => import('./pages/portal/TemplateDetailPage'),
  'TemplateDetailPage',
)
const PortalMyChannels = lazyNamed(() => import('./pages/portal/MyChannelsPage'), 'MyChannelsPage')
const PortalChannelDetail = lazyNamed(
  () => import('./pages/portal/ChannelDetailPage'),
  'ChannelDetailPage',
)
const PortalChannelKnowledge = lazyNamed(
  () => import('./pages/portal/ChannelKnowledgePage'),
  'ChannelKnowledgePage',
)

function PageSuspense({ children }: { children: React.ReactNode }) {
  return (
    <Suspense
      fallback={
        <div className="flex items-center justify-center min-h-[60vh]">
          <Spinner size="lg" />
        </div>
      }
    >
      {children}
    </Suspense>
  )
}

export function PortalRoutes() {
  return (
    <Routes>
      <Route path="/register" element={<PageSuspense><RegisterPage /></PageSuspense>} />
      <Route path="/portal" element={<UserLayout><PageSuspense><PortalDashboard /></PageSuspense></UserLayout>} />
      <Route
        path="/portal/dashboard"
        element={<UserLayout><PageSuspense><PortalDashboard /></PageSuspense></UserLayout>}
      />
      <Route
        path="/portal/templates"
        element={<UserLayout><PageSuspense><PortalTemplates /></PageSuspense></UserLayout>}
      />
      <Route
        path="/portal/templates/:id"
        element={<UserLayout><PageSuspense><PortalTemplateDetail /></PageSuspense></UserLayout>}
      />
      <Route
        path="/portal/channels"
        element={<UserLayout><PageSuspense><PortalMyChannels /></PageSuspense></UserLayout>}
      />
      <Route
        path="/portal/channels/:id"
        element={<UserLayout><PageSuspense><PortalChannelDetail /></PageSuspense></UserLayout>}
      />
      <Route
        path="/portal/channels/:id/knowledge"
        element={<UserLayout><PageSuspense><PortalChannelKnowledge /></PageSuspense></UserLayout>}
      />
    </Routes>
  )
}
