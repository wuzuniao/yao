import request from '../request'

export function login(data) {
  return request.post('/api/v1/users/login', data)
}

export function getUserInfo() {
  return request.get('/api/v1/users/info')
}
