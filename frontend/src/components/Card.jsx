import React from 'react'
import { Card, Badge } from 'react-bootstrap'

export const StatCard = ({
  title,
  value,
  icon,
  color = 'primary',
  trend,
  trendValue,
  subtitle,
  className,
  onClick,
}) => {
  const colorMap = {
    primary: {
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      iconBg: 'rgba(255, 255, 255, 0.2)',
    },
    success: {
      background: 'linear-gradient(135deg, #11998e 0%, #38ef7d 100%)',
      iconBg: 'rgba(255, 255, 255, 0.2)',
    },
    warning: {
      background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
      iconBg: 'rgba(255, 255, 255, 0.2)',
    },
    danger: {
      background: 'linear-gradient(135deg, #ff6b6b 0%, #ee5a5a 100%)',
      iconBg: 'rgba(255, 255, 255, 0.2)',
    },
    info: {
      background: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
      iconBg: 'rgba(255, 255, 255, 0.2)',
    },
  }

  const currentColor = colorMap[color] || colorMap.primary

  return (
    <Card
      className={`border-0 shadow-sm ${className}`}
      style={{
        background: currentColor.background,
        color: 'white',
        cursor: onClick ? 'pointer' : 'default',
        transition: 'transform 0.2s ease, box-shadow 0.2s ease',
      }}
      onClick={onClick}
      onMouseEnter={(e) => {
        if (onClick) {
          e.currentTarget.style.transform = 'translateY(-4px)'
          e.currentTarget.style.boxShadow = '0 8px 16px rgba(0,0,0,0.2)'
        }
      }}
      onMouseLeave={(e) => {
        if (onClick) {
          e.currentTarget.style.transform = 'translateY(0)'
          e.currentTarget.style.boxShadow = '0 2px 4px rgba(0,0,0,0.1)'
        }
      }}
    >
      <Card.Body>
        <div className="d-flex justify-content-between align-items-center">
          <div>
            <Card.Title style={{ fontSize: '0.9rem', opacity: 0.9 }}>{title}</Card.Title>
            <Card.Text style={{ fontSize: '1.8rem', fontWeight: 'bold', margin: 0 }}>
              {value}
            </Card.Text>
            {subtitle && (
              <Card.Text style={{ fontSize: '0.8rem', opacity: 0.8, margin: '4px 0 0 0' }}>
                {subtitle}
              </Card.Text>
            )}
            {trend && (
              <div className="mt-2">
                <Badge bg={trend === 'up' ? 'success' : trend === 'down' ? 'danger' : 'secondary'}>
                  {trend === 'up' ? '↑' : trend === 'down' ? '↓' : '→'} {trendValue}
                </Badge>
              </div>
            )}
          </div>
          <div
            style={{
              fontSize: '2.5rem',
              opacity: 0.8,
              background: currentColor.iconBg,
              borderRadius: '50%',
              width: '60px',
              height: '60px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            {icon}
          </div>
        </div>
      </Card.Body>
    </Card>
  )
}

export const InfoCard = ({ title, children, footer, className, ...props }) => {
  return (
    <Card className={`border-0 shadow-sm ${className}`} {...props}>
      {title && (
        <Card.Header className="bg-white border-0 fw-bold py-3">{title}</Card.Header>
      )}
      <Card.Body>{children}</Card.Body>
      {footer && <Card.Footer className="bg-white border-0">{footer}</Card.Footer>}
    </Card>
  )
}

export const ChartCard = ({ title, children, headerAction, className }) => {
  return (
    <Card className={`border-0 shadow-sm ${className}`}>
      {title && (
        <Card.Header className="bg-white border-0 fw-bold py-3">
          <div className="d-flex justify-content-between align-items-center">
            <span>{title}</span>
            {headerAction && <div>{headerAction}</div>}
          </div>
        </Card.Header>
      )}
      <Card.Body>{children}</Card.Body>
    </Card>
  )
}

export default {
  StatCard,
  InfoCard,
  ChartCard,
}
