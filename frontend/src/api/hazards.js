import http from './http'

export const fetchHazards = (params) => http.get('/hazards', { params })

export const fetchHazard = (id) => http.get(`/hazards/${id}`)

export const createHazard = (payload) => http.post('/hazards', payload)

export const assignHazard = (id, payload) => http.patch(`/hazards/${id}/assign`, payload)

export const submitRectification = (id, payload) =>
  http.patch(`/hazards/${id}/rectification`, payload)

export const submitAcceptance = (id, payload) =>
  http.patch(`/hazards/${id}/acceptance`, payload)

export const fetchStatistics = () => http.get('/hazards/statistics')

export const fetchHazardOptions = () => http.get('/hazards/options')
