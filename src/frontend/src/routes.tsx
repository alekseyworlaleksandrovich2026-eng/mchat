import { lazy, Suspense } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { isCloudEdition } from '@/lib/edition'
import { AdminLayout } from './components/layout/AdminLayout'
import { Spinner } from './components/ui/Spinner'
import { DocumentTitle } from './components/common/DocumentTitle'

const lazyNamed = <T extends Record<string, React.ComponentType<any>>>(
  loader: () => Promise<T>,
  name: keyof T
) => lazy(() => loader().then(m => ({ default: m[name] })))

const LandingPage = lazyNamed(() => import('./pages/LandingPage'), 'LandingPage')
const AdminLogin = lazyNamed(() => import('./pages/AdminLogin'), 'AdminLogin')
const AdminDashboard = lazyNamed(() => import('./pages/AdminDashboard'), 'AdminDashboard')
const ConversationsPage = lazyNamed(() => import('./pages/ConversationsPage'), 'ConversationsPage')
const KnowledgePage = lazyNamed(() => import('./pages/KnowledgePage'), 'KnowledgePage')
const SkillsPage = lazyNamed(() => import('./pages/SkillsPage'), 'SkillsPage')
const AgentsPage = lazyNamed(() => import('./pages/AgentsPage'), 'AgentsPage')
const CustomerAgentsPage = lazyNamed(() => import('./pages/CustomerAgentsPage'), 'CustomerAgentsPage')
const SettingsPage = lazyNamed(() => import('./pages/SettingsPage'), 'SettingsPage')
const ChannelsPage = lazyNamed(() => import('./pages/ChannelsPage'), 'ChannelsPage')
const ChatPage = lazyNamed(() => import('./pages/ChatPage'), 'ChatPage')
const WidgetDemo = lazyNamed(() => import('./pages/WidgetDemo'), 'WidgetDemo')
const WidgetPage = lazyNamed(() => import('./pages/WidgetPage'), 'WidgetPage')
const SkillShowcasePage = lazyNamed(() => import('./pages/SkillShowcasePage'), 'SkillShowcasePage')
const WxMiniPage = lazyNamed(() => import('./pages/WxMiniPage'), 'WxMiniPage')
const MpJump = lazyNamed(() => import('./pages/MpJump'), 'MpJump')
const HelpPage = lazyNamed(() => import('./pages/HelpPage'), 'HelpPage')
const UsersPage = lazyNamed(() => import('./pages/UsersPage'), 'UsersPage')
const RolesPage = lazyNamed(() => import('./pages/RolesPage'), 'RolesPage')
const TemplateManagerPage = lazyNamed(() => import('./pages/admin/TemplateManagerPage'), 'TemplateManagerPage')

export function PageSuspense({ children }: { children: React.ReactNode }) {
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

export function CoreRoutes() {
  return (
    <>
      <DocumentTitle />
      <Routes>
        <Route path="/" element={<PageSuspense><LandingPage /></PageSuspense>} />
        <Route path="/admin/login" element={<PageSuspense><AdminLogin /></PageSuspense>} />
        <Route path="/admin" element={<AdminLayout><PageSuspense><AdminDashboard /></PageSuspense></AdminLayout>} />
        <Route path="/admin/conversations" element={<AdminLayout><PageSuspense><ConversationsPage /></PageSuspense></AdminLayout>} />
        <Route path="/admin/knowledge" element={<AdminLayout><PageSuspense><KnowledgePage /></PageSuspense></AdminLayout>} />
        <Route path="/admin/skills" element={<AdminLayout><PageSuspense><SkillsPage /></PageSuspense></AdminLayout>} />
        <Route path="/admin/agents" element={<AdminLayout><PageSuspense><AgentsPage /></PageSuspense></AdminLayout>} />
        <Route path="/admin/customer-agents" element={<AdminLayout><PageSuspense><CustomerAgentsPage /></PageSuspense></AdminLayout>} />
        <Route path="/admin/settings" element={<AdminLayout><PageSuspense><SettingsPage /></PageSuspense></AdminLayout>} />
        <Route path="/admin/channels" element={<AdminLayout><PageSuspense><ChannelsPage /></PageSuspense></AdminLayout>} />
        <Route path="/admin/roles" element={<AdminLayout><PageSuspense><RolesPage /></PageSuspense></AdminLayout>} />
        {isCloudEdition ? (
          <Route path="/admin/templates" element={<AdminLayout><PageSuspense><TemplateManagerPage /></PageSuspense></AdminLayout>} />
        ) : (
          <Route path="/admin/templates" element={<Navigate to="/admin" replace />} />
        )}
        <Route path="/admin/users" element={<AdminLayout><PageSuspense><UsersPage /></PageSuspense></AdminLayout>} />
        <Route path="/chat/:conversationId" element={<PageSuspense><ChatPage /></PageSuspense>} />
        <Route path="/widget/demo" element={<PageSuspense><WidgetDemo /></PageSuspense>} />
        <Route path="/widget" element={<PageSuspense><WidgetPage /></PageSuspense>} />
        <Route path="/wx-mini" element={<PageSuspense><WxMiniPage /></PageSuspense>} />
        <Route path="/mini-program" element={<PageSuspense><MpJump /></PageSuspense>} />
        <Route path="/help" element={<PageSuspense><HelpPage /></PageSuspense>} />
        <Route path="/showcase" element={<PageSuspense><SkillShowcasePage /></PageSuspense>} />
      </Routes>
    </>
  )
}
