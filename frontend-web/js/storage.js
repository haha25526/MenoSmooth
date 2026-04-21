// LocalStorage wrapper
const storage = {
  get(key, def = null) {
    try {
      const v = localStorage.getItem(key);
      return v !== null ? JSON.parse(v) : def;
    } catch { return def; }
  },
  set(key, value) {
    try { localStorage.setItem(key, JSON.stringify(value)); return true; }
    catch { return false; }
  },
  remove(key) { localStorage.removeItem(key); },
  clear() { ['access_token', 'refresh_token', 'user'].forEach(k => localStorage.removeItem(k)); },
  isLoggedIn() { return !!this.get('access_token'); },
  getUser() { return this.get('user'); },
};
