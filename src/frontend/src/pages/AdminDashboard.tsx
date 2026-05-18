import React, { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import {
  MessageSquare,
  Bot,
  BookOpen,
  Puzzle,
  TrendingUp,
  Clock,
  ArrowUp,
  ArrowDown,
} from 'lucide-react'
import api from '@/lib/api'
import { Card, CardContent } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { formatDate } from '@/lib/utils'

interface DashboardStats {
  total_conversations: number
  active_conversations: number
  total_agents: number
  total_documents: number
  total_skills: number
  messages_today: number
  avg_response_time: number
  satisfaction_rate: number
  trends: {
    conversations: number
    messages: number
    documents: number
  }
}

interface RecentActivity {
  id: string
  type: 'conversation' | 'message' | 'document' | 'skill'
  description: string
  timestamp: string
}

export function AdminDashboard() {
  const { t } = useTranslation()
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [activities, setActivities] = useState<RecentActivity[]>([])
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState<string | null>(null)

  useEffect(() => {
    Promise.all([loadStats(), loadActivities()]).finally(() =>
      setLoading(false),
    )
  }, [])

  const loadStats = async () => {
    try {
      const data = await api.get<DashboardStats>('/dashboard/stats')
      setStats(data)
      setLoadError(null)
    } catch (err) {
      console.error('Failed to load stats:', err)
      setLoadError(t('dashboard.loadError'))
      setStats({
        total_conversations: 0,
        active_conversations: 0,
        total_agents: 0,
        total_documents: 0,
        total_skills: 0,
        messages_today: 0,
        avg_response_time: 0,
        satisfaction_rate: 0,
        trends: { conversations: 0, messages: 0, documents: 0 },
      })
    }
  }

  const loadActivities = async () => {
    try {
      const data = await api.get<RecentActivity[]>('/dashboard/activities')
      setActivities(data)
    } catch (err) {
      console.error('Failed to load activities:', err)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="w-10 h-10 border-4 border-primary-600 border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  if (!stats) {
    return (
      <div className="text-center py-20 text-gray-500">
        {loadError || t('dashboard.noData')}
      </div>
    )
  }

  const s = stats
  const statCards = [
    {
      labelKey: 'dashboard.totalConversations',
      value: s.total_conversations,
      icon: MessageSquare,
      color: 'text-blue-600 bg-blue-100 dark:bg-blue-900/30',
      trend: s.trends.conversations,
    },
    {
      labelKey: 'dashboard.activeConversations',
      value: s.active_conversations,
      icon: Clock,
      color: 'text-green-600 bg-green-100 dark:bg-green-900/30',
      trend: 0,
    },
    {
      labelKey: 'dashboard.totalAgents',
      value: s.total_agents,
      icon: Bot,
      color: 'text-purple-600 bg-purple-100 dark:bg-purple-900/30',
      trend: 0,
    },
    {
      labelKey: 'dashboard.totalDocuments',
      value: s.total_documents,
      icon: BookOpen,
      color: 'text-orange-600 bg-orange-100 dark:bg-orange-900/30',
      trend: s.trends.documents,
    },
    {
      labelKey: 'dashboard.totalSkills',
      value: s.total_skills,
      icon: Puzzle,
      color: 'text-teal-600 bg-teal-100 dark:bg-teal-900/30',
      trend: 0,
    },
    {
      labelKey: 'dashboard.messagesToday',
      value: s.messages_today,
      icon: TrendingUp,
      color: 'text-pink-600 bg-pink-100 dark:bg-pink-900/30',
      trend: s.trends.messages,
    },
  ] as const

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
          {t('dashboard.title')}
        </h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
          {t('dashboard.subtitle')}
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
        {statCards.map((card) => (
          <Card key={card.labelKey}>
            <CardContent className="py-4">
              <div className="flex items-center justify-between mb-3">
                <div className={`p-2 rounded-lg ${card.color}`}>
                  <card.icon className="w-5 h-5" />
                </div>
                {card.trend !== 0 && (
                  <Badge
                    variant={card.trend > 0 ? 'success' : 'danger'}
                    size="sm"
                  >
                    <span className="flex items-center gap-0.5">
                      {card.trend > 0 ? (
                        <ArrowUp className="w-3 h-3" />
                      ) : (
                        <ArrowDown className="w-3 h-3" />
                      )}
                      {Math.abs(card.trend)}%
                    </span>
                  </Badge>
                )}
              </div>
              <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                {card.value.toLocaleString()}
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                {t(card.labelKey)}
              </p>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardContent className="py-4">
            <h3 className="font-medium text-gray-900 dark:text-gray-100 mb-4">
              {t('dashboard.performance')}
            </h3>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600 dark:text-gray-400">
                  {t('dashboard.avgResponse')}
                </span>
                <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
                  {s.avg_response_time < 1000
                    ? `${s.avg_response_time}ms`
                    : `${(s.avg_response_time / 1000).toFixed(1)}s`}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600 dark:text-gray-400">
                  {t('dashboard.satisfaction')}
                </span>
                <span className="text-sm font-medium text-green-600">
                  {s.satisfaction_rate}%
                </span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="py-4">
            <h3 className="font-medium text-gray-900 dark:text-gray-100 mb-4">
              {t('dashboard.recentActivity')}
            </h3>
            {activities.length === 0 ? (
              <p className="text-sm text-gray-400 text-center py-4">
                {t('dashboard.noActivity')}
              </p>
            ) : (
              <div className="space-y-3">
                {activities.slice(0, 5).map((activity) => (
                  <div
                    key={activity.id}
                    className="flex items-center gap-3 text-sm"
                  >
                    <div className="w-2 h-2 rounded-full bg-primary-500 shrink-0" />
                    <div className="flex-1 min-w-0">
                      <p className="text-gray-700 dark:text-gray-300 truncate">
                        {activity.description}
                      </p>
                      <p className="text-xs text-gray-400">
                        {formatDate(activity.timestamp)}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
