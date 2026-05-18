import { type HTMLAttributes, forwardRef } from 'react'
import { cn } from '../../lib/cn'

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: 'default' | 'primary' | 'success' | 'warning' | 'danger'
}

export const Badge = forwardRef<HTMLSpanElement, BadgeProps>(
  ({ className, variant = 'default', children, ...props }, ref) => {
    return (
      <span
        ref={ref}
        className={cn(
          'inline-flex items-center px-2 py-0.5 rounded text-xs font-medium',
          {
            'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300': variant === 'default',
            'bg-primary-100 text-primary-700 dark:bg-primary-900 dark:text-primary-300': variant === 'primary',
            'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300': variant === 'success',
            'bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300': variant === 'warning',
            'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300': variant === 'danger',
          },
          className
        )}
        {...props}
      >
        {children}
      </span>
    )
  }
)

Badge.displayName = 'Badge'
