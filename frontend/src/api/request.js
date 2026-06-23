const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const request = {
  get(url, params = {}) {
    return uni.request({
      url: BASE_URL + url,
      method: 'GET',
      data: params
    })
  },

  post(url, data = {}) {
    return uni.request({
      url: BASE_URL + url,
      method: 'POST',
      data
    })
  },

  put(url, data = {}) {
    return uni.request({
      url: BASE_URL + url,
      method: 'PUT',
      data
    })
  },

  delete(url, data = {}) {
    return uni.request({
      url: BASE_URL + url,
      method: 'DELETE',
      data
    })
  }
}

export default request
