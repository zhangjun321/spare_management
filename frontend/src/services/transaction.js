import axios from 'axios'

const prefix = '/api/transactions'

export const fetchTransactions = (params = {}) => {
  return axios.get(prefix, { params })
}

export const fetchTransactionDetail = (id) => {
  return axios.get(`${prefix}/${id}`)
}

export const createTransaction = (payload) => {
  return axios.post(prefix, payload)
}

export const submitTransaction = (id) => {
  return axios.post(`${prefix}/${id}/submit`)
}

export const approveTransaction = (id) => {
  return axios.post(`${prefix}/${id}/approve`)
}

export const rejectTransaction = (id, reason) => {
  return axios.post(`${prefix}/${id}/reject`, { reason })
}

export const validateTransaction = (payload) => {
  return axios.post(`${prefix}/validate`, payload)
}

export const exportTransactions = (params = {}) => {
  return axios.get(`${prefix}/export`, { params, responseType: 'blob' })
}
