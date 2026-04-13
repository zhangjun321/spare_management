import React from 'react'
import { Button as BootstrapButton, Spinner } from 'react-bootstrap'

export const Button = ({
  children,
  variant = 'primary',
  size = 'md',
  loading = false,
  disabled = false,
  onClick,
  className,
  ...props
}) => {
  return (
    <BootstrapButton
      variant={variant}
      size={size}
      disabled={disabled || loading}
      onClick={onClick}
      className={className}
      {...props}
    >
      {loading ? (
        <>
          <Spinner as="span" animation="border" size="sm" role="status" aria-hidden="true" />
          <span className="ms-2">加载中...</span>
        </>
      ) : (
        children
      )}
    </BootstrapButton>
  )
}

export const IconButton = ({ icon, children, variant = 'outline-secondary', size = 'sm', ...props }) => {
  return (
    <Button variant={variant} size={size} {...props}>
      {icon}
      {children && <span className="ms-1">{children}</span>}
    </Button>
  )
}

export const ActionButton = ({ action, item, ...props }) => {
  const handleClick = (e) => {
    e.stopPropagation()
    action.onClick(item)
  }

  return (
    <Button
      variant={action.variant || 'outline-primary'}
      size="sm"
      onClick={handleClick}
      {...props}
    >
      {action.icon}
      {action.label && <span className="ms-1">{action.label}</span>}
    </Button>
  )
}

export const ActionButtons = ({ actions = [], item, className }) => {
  return (
    <div className={`d-flex gap-2 ${className}`}>
      {actions.map((action, index) => (
        <ActionButton key={index} action={action} item={item} />
      ))}
    </div>
  )
}

export default {
  Button,
  IconButton,
  ActionButton,
  ActionButtons,
}
