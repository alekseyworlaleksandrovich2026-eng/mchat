import type React from 'react'
import type { TFunction } from 'i18next'
import { Globe, MessageCircle, Settings2 } from 'lucide-react'

export type ChannelFieldDef = {
  key: string
  label: string
  placeholder: string
  type?: string
}

export type ChannelTypeDef = {
  label: string
  icon: React.FC<{ className?: string }>
  description: string
  fields: ChannelFieldDef[]
}

export function getChannelTypes(t: TFunction): Record<string, ChannelTypeDef> {
  return {
    web_widget: {
      label: t('channels.types.web_widget.label'),
      icon: Globe,
      description: t('channels.types.web_widget.description'),
      fields: [
        {
          key: 'widget_id',
          label: t('channels.types.web_widget.fields.widget_id.label'),
          placeholder: t('channels.types.web_widget.fields.widget_id.placeholder'),
        },
      ],
    },
    wechat: {
      label: t('channels.types.wechat.label'),
      icon: MessageCircle,
      description: t('channels.types.wechat.description'),
      fields: [
        {
          key: 'customer_id',
          label: t('channels.types.wechat.fields.customer_id.label'),
          placeholder: t('channels.types.wechat.fields.customer_id.placeholder'),
        },
        {
          key: 'app_id',
          label: t('channels.types.wechat.fields.app_id.label'),
          placeholder: t('channels.types.wechat.fields.app_id.placeholder'),
        },
        {
          key: 'app_secret',
          label: t('channels.types.wechat.fields.app_secret.label'),
          placeholder: t('channels.types.wechat.fields.app_secret.placeholder'),
          type: 'password',
        },
        {
          key: 'token',
          label: t('channels.types.wechat.fields.token.label'),
          placeholder: t('channels.types.wechat.fields.token.placeholder'),
        },
        {
          key: 'encoding_aes_key',
          label: t('channels.types.wechat.fields.encoding_aes_key.label'),
          placeholder: t('channels.types.wechat.fields.encoding_aes_key.placeholder'),
        },
      ],
    },
    dingtalk: {
      label: t('channels.types.dingtalk.label'),
      icon: MessageCircle,
      description: t('channels.types.dingtalk.description'),
      fields: [
        {
          key: 'app_key',
          label: t('channels.types.dingtalk.fields.app_key.label'),
          placeholder: t('channels.types.dingtalk.fields.app_key.placeholder'),
        },
        {
          key: 'app_secret',
          label: t('channels.types.dingtalk.fields.app_secret.label'),
          placeholder: t('channels.types.dingtalk.fields.app_secret.placeholder'),
          type: 'password',
        },
        {
          key: 'webhook_url',
          label: t('channels.types.dingtalk.fields.webhook_url.label'),
          placeholder: t('channels.types.dingtalk.fields.webhook_url.placeholder'),
        },
      ],
    },
    whatsapp: {
      label: t('channels.types.whatsapp.label'),
      icon: MessageCircle,
      description: t('channels.types.whatsapp.description'),
      fields: [
        {
          key: 'phone_number_id',
          label: t('channels.types.whatsapp.fields.phone_number_id.label'),
          placeholder: t('channels.types.whatsapp.fields.phone_number_id.placeholder'),
        },
        {
          key: 'access_token',
          label: t('channels.types.whatsapp.fields.access_token.label'),
          placeholder: t('channels.types.whatsapp.fields.access_token.placeholder'),
          type: 'password',
        },
        {
          key: 'verify_token',
          label: t('channels.types.whatsapp.fields.verify_token.label'),
          placeholder: t('channels.types.whatsapp.fields.verify_token.placeholder'),
        },
      ],
    },
    telegram: {
      label: t('channels.types.telegram.label'),
      icon: MessageCircle,
      description: t('channels.types.telegram.description'),
      fields: [
        {
          key: 'bot_token',
          label: t('channels.types.telegram.fields.bot_token.label'),
          placeholder: t('channels.types.telegram.fields.bot_token.placeholder'),
          type: 'password',
        },
      ],
    },
    slack: {
      label: t('channels.types.slack.label'),
      icon: MessageCircle,
      description: t('channels.types.slack.description'),
      fields: [
        {
          key: 'bot_token',
          label: t('channels.types.slack.fields.bot_token.label'),
          placeholder: t('channels.types.slack.fields.bot_token.placeholder'),
          type: 'password',
        },
        {
          key: 'signing_secret',
          label: t('channels.types.slack.fields.signing_secret.label'),
          placeholder: t('channels.types.slack.fields.signing_secret.placeholder'),
          type: 'password',
        },
      ],
    },
    line: {
      label: t('channels.types.line.label'),
      icon: MessageCircle,
      description: t('channels.types.line.description'),
      fields: [
        {
          key: 'channel_access_token',
          label: t('channels.types.line.fields.channel_access_token.label'),
          placeholder: t('channels.types.line.fields.channel_access_token.placeholder'),
          type: 'password',
        },
        {
          key: 'channel_secret',
          label: t('channels.types.line.fields.channel_secret.label'),
          placeholder: t('channels.types.line.fields.channel_secret.placeholder'),
          type: 'password',
        },
      ],
    },
    custom: {
      label: t('channels.types.custom.label'),
      icon: Settings2,
      description: t('channels.types.custom.description'),
      fields: [
        {
          key: 'webhook_url',
          label: t('channels.types.custom.fields.webhook_url.label'),
          placeholder: t('channels.types.custom.fields.webhook_url.placeholder'),
        },
        {
          key: 'api_key',
          label: t('channels.types.custom.fields.api_key.label'),
          placeholder: t('channels.types.custom.fields.api_key.placeholder'),
          type: 'password',
        },
      ],
    },
  }
}
