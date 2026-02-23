import { cn } from '@/lib/utils'

export type CompletionStatus = 'followed' | 'equivalent' | 'skipped' | 'deviated' | 'social' | 'pending'

interface StatusBadgeProps {
  status: CompletionStatus
  className?: string
}

const statusConfig = {
  followed: {
    label: 'Followed',
    className: 'bg-success/10 text-success border-success/20',
    icon: (
      <svg
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 16 16"
        fill="currentColor"
        className="h-3 w-3"
      >
        <path
          fillRule="evenodd"
          d="M12.416 3.376a.75.75 0 0 1 .208 1.04l-5 7.5a.75.75 0 0 1-1.154.114l-3-3a.75.75 0 0 1 1.06-1.06l2.353 2.353 4.493-6.74a.75.75 0 0 1 1.04-.207Z"
          clipRule="evenodd"
        />
      </svg>
    ),
  },
  equivalent: {
    label: 'Equivalent',
    className: 'bg-warning/10 text-warning border-warning/20',
    icon: (
      <svg
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 16 16"
        fill="currentColor"
        className="h-3 w-3"
      >
        <path d="M8.75 3.75a.75.75 0 0 0-1.5 0v3.5h-3.5a.75.75 0 0 0 0 1.5h3.5v3.5a.75.75 0 0 0 1.5 0v-3.5h3.5a.75.75 0 0 0 0-1.5h-3.5v-3.5Z" />
      </svg>
    ),
  },
  skipped: {
    label: 'Skipped',
    className: 'bg-muted text-muted-foreground border-border',
    icon: (
      <svg
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 16 16"
        fill="currentColor"
        className="h-3 w-3"
      >
        <path d="M6.22 4.22a.75.75 0 0 1 1.06 0L10.06 7l-2.78 2.78a.75.75 0 0 1-1.06-1.06L7.44 7.5H3.75a.75.75 0 0 1 0-1.5h3.69L6.22 4.78a.75.75 0 0 1 0-1.06Z" />
        <path d="M12 7.5a.75.75 0 0 1 .75.75v.75h-.75a.75.75 0 0 1 0-1.5Z" />
      </svg>
    ),
  },
  deviated: {
    label: 'Deviated',
    className: 'bg-destructive/10 text-destructive border-destructive/20',
    icon: (
      <svg
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 16 16"
        fill="currentColor"
        className="h-3 w-3"
      >
        <path
          fillRule="evenodd"
          d="M13.836 2.477a.75.75 0 0 1 .75.75v4.796a.75.75 0 0 1-.75.75h-4.796a.75.75 0 0 0 0 1.5h2.966l-5.469 5.47a.75.75 0 1 1-1.061-1.061l5.469-5.47v2.967a.75.75 0 0 0 1.5 0V3.227a.75.75 0 0 1 .75-.75Z"
          clipRule="evenodd"
        />
      </svg>
    ),
  },
  social: {
    label: 'Social',
    className: 'bg-primary/10 text-primary border-primary/20',
    icon: (
      <svg
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 16 16"
        fill="currentColor"
        className="h-3 w-3"
      >
        <path d="M8 8a3 3 0 1 0 0-6 3 3 0 0 0 0 6ZM12.5 16h.5a2 2 0 0 0 2-2v-.5a2.5 2.5 0 0 0-2.5-2.5h-3v5ZM3.5 11A2.5 2.5 0 0 0 1 13.5v.5a2 2 0 0 0 2 2h.5v-5h-3Z" />
      </svg>
    ),
  },
  pending: {
    label: 'Pending',
    className: 'bg-card text-muted-foreground border-border',
    icon: (
      <svg
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 16 16"
        fill="currentColor"
        className="h-3 w-3"
      >
        <path
          fillRule="evenodd"
          d="M8 14A6 6 0 1 0 8 2a6 6 0 0 0 0 12Zm.75-8.25a.75.75 0 0 0-1.5 0V8c0 .414.336.75.75.75h2a.75.75 0 0 0 0-1.5h-1.25V5.75Z"
          clipRule="evenodd"
        />
      </svg>
    ),
  },
}

export function StatusBadge({ status, className }: StatusBadgeProps) {
  const config = statusConfig[status]

  return (
    <div
      className={cn(
        'inline-flex items-center gap-1.5 rounded-md border px-2.5 py-1 text-xs font-medium',
        config.className,
        className
      )}
    >
      {config.icon}
      <span>{config.label}</span>
    </div>
  )
}
