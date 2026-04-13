import React from 'react'
import { Form as BootstrapForm } from 'react-bootstrap'

export const FormField = ({
  label,
  type = 'text',
  value,
  onChange,
  placeholder,
  required = false,
  error,
  helpText,
  disabled = false,
  className,
  ...props
}) => {
  return (
    <BootstrapForm.Group className={`mb-3 ${className}`}>
      {label && (
        <BootstrapForm.Label>
          {label}
          {required && <span className="text-danger ms-1">*</span>}
        </BootstrapForm.Label>
      )}
      <BootstrapForm.Control
        type={type}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        disabled={disabled}
        isInvalid={!!error}
        {...props}
      />
      {error && <BootstrapForm.Control.Feedback type="invalid">{error}</BootstrapForm.Control.Feedback>}
      {helpText && !error && <BootstrapForm.Text className="text-muted">{helpText}</BootstrapForm.Text>}
    </BootstrapForm.Group>
  )
}

export const SelectField = ({
  label,
  value,
  onChange,
  options = [],
  placeholder = '请选择',
  required = false,
  error,
  disabled = false,
  className,
  ...props
}) => {
  return (
    <BootstrapForm.Group className={`mb-3 ${className}`}>
      {label && (
        <BootstrapForm.Label>
          {label}
          {required && <span className="text-danger ms-1">*</span>}
        </BootstrapForm.Label>
      )}
      <BootstrapForm.Select
        value={value}
        onChange={onChange}
        disabled={disabled}
        isInvalid={!!error}
        {...props}
      >
        <option value="">{placeholder}</option>
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </BootstrapForm.Select>
      {error && <BootstrapForm.Control.Feedback type="invalid">{error}</BootstrapForm.Control.Feedback>}
    </BootstrapForm.Group>
  )
}

export const TextAreaField = ({
  label,
  value,
  onChange,
  placeholder,
  required = false,
  error,
  rows = 3,
  disabled = false,
  className,
  ...props
}) => {
  return (
    <BootstrapForm.Group className={`mb-3 ${className}`}>
      {label && (
        <BootstrapForm.Label>
          {label}
          {required && <span className="text-danger ms-1">*</span>}
        </BootstrapForm.Label>
      )}
      <BootstrapForm.Control
        as="textarea"
        rows={rows}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        disabled={disabled}
        isInvalid={!!error}
        {...props}
      />
      {error && <BootstrapForm.Control.Feedback type="invalid">{error}</BootstrapForm.Control.Feedback>}
    </BootstrapForm.Group>
  )
}

export const CheckboxField = ({
  label,
  checked,
  onChange,
  disabled = false,
  className,
  ...props
}) => {
  return (
    <BootstrapForm.Group className={`mb-3 ${className}`}>
      <BootstrapForm.Check
        type="checkbox"
        label={label}
        checked={checked}
        onChange={onChange}
        disabled={disabled}
        {...props}
      />
    </BootstrapForm.Group>
  )
}

export const RadioField = ({
  label,
  options = [],
  value,
  onChange,
  disabled = false,
  className,
  ...props
}) => {
  return (
    <BootstrapForm.Group className={`mb-3 ${className}`}>
      {label && <BootstrapForm.Label>{label}</BootstrapForm.Label>}
      {options.map((option) => (
        <BootstrapForm.Check
          key={option.value}
          type="radio"
          label={option.label}
          name={label}
          value={option.value}
          checked={value === option.value}
          onChange={onChange}
          disabled={disabled}
          inline
          {...props}
        />
      ))}
    </BootstrapForm.Group>
  )
}

export const Form = ({ children, onSubmit, className, ...props }) => {
  const handleSubmit = (e) => {
    e.preventDefault()
    onSubmit && onSubmit(e)
  }

  return (
    <BootstrapForm onSubmit={handleSubmit} className={className} {...props}>
      {children}
    </BootstrapForm>
  )
}

export default {
  Form,
  FormField,
  SelectField,
  TextAreaField,
  CheckboxField,
  RadioField,
}
