import http from './http'

export function fetchHazards(params) {
  return http.get('/hazards', { params })
}

export function fetchHazardDetail(id) {
  return http.get(`/hazards/${id}`)
}

export function createHazard(payload) {
  return http.post('/hazards', payload)
}

export function assignHazard(id, payload) {
  return http.patch(`/hazards/${id}/assign`, payload)
}

export function submitRectification(id, payload) {
  return http.patch(`/hazards/${id}/rectification`, payload)
}

export function acceptHazard(id, payload) {
  return http.patch(`/hazards/${id}/acceptance`, payload)
}

export function fetchStatistics() {
  return http.get('/hazards/statistics')
}

export function fetchDictionaries() {
  return http.get('/hazards/dictionaries')
}
