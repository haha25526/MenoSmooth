// API client with JWT token
const API_BASE = '/api/v1';

const api = {
  async request(method, path, data = null) {
    const headers = { 'Content-Type': 'application/json' };
    const token = storage.get('access_token');
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const opts = { method, headers };
    if (data && method !== 'GET') opts.body = JSON.stringify(data);

    const res = await fetch(`${API_BASE}${path}`, opts);
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: '请求失败' }));
      if (res.status === 401) {
        storage.clear();
        window.location.href = '/meno/';
        throw new Error('登录已过期，请重新登录');
      }
      throw new Error(err.detail || '请求失败');
    }
    return res.json();
  },

  get(path) { return this.request('GET', path); },
  post(path, data) { return this.request('POST', path, data); },
  put(path, data) { return this.request('PUT', path, data); },
  del(path) { return this.request('DELETE', path); },

  // File upload
  async uploadFile(path, file, extra = {}) {
    const formData = new FormData();
    formData.append('image', file);
    const headers = {};
    const token = storage.get('access_token');
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const res = await fetch(`${API_BASE}${path}`, { method: 'POST', headers, body: formData });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: '上传失败' }));
      throw new Error(err.detail || '上传失败');
    }
    return res.json();
  },

  // Analytics
  trackPage(pageName) {
    navigator.sendBeacon && navigator.sendBeacon(
      `${API_BASE}/analytics/page-views/increment`,
      JSON.stringify({ page_name: pageName, session_id: this.getSessionId() })
    );
  },

  getSessionId() {
    let sid = sessionStorage.getItem('session_id');
    if (!sid) {
      sid = 'sess_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
      sessionStorage.setItem('session_id', sid);
    }
    return sid;
  },
};
