import { Routes, Route, Navigate } from 'react-router-dom'
import { AdminLayout } from './components/layout/AdminLayout'
import { AdminDashboard } from './pages/AdminDashboard'
import { AdminLogin } from './pages/AdminLogin'
import { ConversationsPage } from './pages/ConversationsPage'
import { KnowledgePage } from './pages/KnowledgePage'
import { SkillsPage } from './pages/SkillsPage'
import { AgentsPage } from './pages/AgentsPage'
import { CustomerAgentsPage } from './pages/CustomerAgentsPage'
import { SettingsPage } from './pages/SettingsPage'
import { ChannelsPage } from './pages/ChannelsPage'
import { ChatPage } from './pages/ChatPage'
import { WidgetDemo } from './pages/WidgetDemo'
import { WidgetPage } from './pages/WidgetPage'
import { SkillShowcasePage } from './pages/SkillShowcasePage'
import { LandingPage } from './pages/LandingPage'
import { UsersPage } from './pages/UsersPage'
import { DocumentTitle } from './components/common/DocumentTitle'

export default function App() {
  return (
    <>
    <DocumentTitle />
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/admin/login" element={<AdminLogin />} />
      <Route
        path="/admin"
        element={
          <AdminLayout>
            <AdminDashboard />
          </AdminLayout>
        }
      />
      <Route
        path="/admin/conversations"
        element={
          <AdminLayout>
            <ConversationsPage />
          </AdminLayout>
        }
      />
      <Route
        path="/admin/knowledge"
        element={
          <AdminLayout>
            <KnowledgePage />
          </AdminLayout>
        }
      />
      <Route
        path="/admin/skills"
        element={
          <AdminLayout>
            <SkillsPage />
          </AdminLayout>
        }
      />
      <Route
        path="/admin/agents"
        element={
          <AdminLayout>
            <AgentsPage />
          </AdminLayout>
        }
      />
      <Route
        path="/admin/customer-agents"
        element={
          <AdminLayout>
            <CustomerAgentsPage />
          </AdminLayout>
        }
      />
      <Route
        path="/admin/settings"
        element={
          <AdminLayout>
            <SettingsPage />
          </AdminLayout>
        }
      />
      <Route
        path="/admin/channels"
        element={
          <AdminLayout>
            <ChannelsPage />
          </AdminLayout>
        }
      />
      <Route
        path="/admin/users"
        element={
          <AdminLayout>
            <UsersPage />
          </AdminLayout>
        }
      />
      <Route path="/chat/:conversationId" element={<ChatPage />} />
      <Route path="/widget/demo" element={<WidgetDemo />} />
      <Route path="/widget" element={<WidgetPage />} />
      <Route path="/showcase" element={<SkillShowcasePage />} />
    </Routes>
    </>
  )
}
