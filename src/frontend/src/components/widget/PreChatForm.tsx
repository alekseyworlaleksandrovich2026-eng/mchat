import React, { useState } from 'react'

export type PreChatField = {
  key: string
  label: string
  required?: boolean
  type?: string
}

type PreChatFormProps = {
  fields: PreChatField[]
  accentColor: string
  onSubmit: (values: Record<string, string>) => void
}

export function PreChatForm({ fields, accentColor, onSubmit }: PreChatFormProps) {
  const [values, setValues] = useState<Record<string, string>>({})
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    for (const field of fields) {
      if (field.required && !(values[field.key] || '').trim()) {
        setError(`请填写${field.label}`)
        return
      }
    }
    setError(null)
    onSubmit(values)
  }

  return (
    <form onSubmit={handleSubmit} className="p-4 space-y-3">
      <p className="text-sm text-gray-600 dark:text-gray-300">
        开始前请填写以下信息，以便我们更好地为您服务。
      </p>
      {fields.map((field) => (
        <label key={field.key} className="block text-sm">
          <span className="text-gray-700 dark:text-gray-200">
            {field.label}
            {field.required ? ' *' : ''}
          </span>
          <input
            type={field.type || 'text'}
            className="mt-1 w-full rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 px-3 py-2 text-sm"
            value={values[field.key] || ''}
            onChange={(e) =>
              setValues((prev) => ({ ...prev, [field.key]: e.target.value }))
            }
          />
        </label>
      ))}
      {error && <p className="text-xs text-red-600">{error}</p>}
      <button
        type="submit"
        className="w-full rounded-lg px-3 py-2 text-sm font-medium text-white"
        style={{ backgroundColor: accentColor }}
      >
        开始对话
      </button>
    </form>
  )
}
