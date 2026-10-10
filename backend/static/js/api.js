/**
 * Client API Vanilla JS — fetch() + JWT
 */
(function (global) {
  const TOKEN_KEY = 'gb_access';
  const REFRESH_KEY = 'gb_refresh';
  const USER_KEY = 'gb_user';

  const Api = {
    getToken() {
      return localStorage.getItem(TOKEN_KEY);
    },

    getUser() {
      try {
        return JSON.parse(localStorage.getItem(USER_KEY) || 'null');
      } catch {
        return null;
      }
    },

    setSession(data) {
      localStorage.setItem(TOKEN_KEY, data.access);
      if (data.refresh) localStorage.setItem(REFRESH_KEY, data.refresh);
      const user = {
        id: data.id,
        username: data.username,
        role: data.role,
        is_staff_role: data.is_staff_role,
        is_client_role: data.is_client_role,
        membre_id: data.membre_id,
      };
      localStorage.setItem(USER_KEY, JSON.stringify(user));
      return user;
    },

    clearSession() {
      localStorage.removeItem(TOKEN_KEY);
      localStorage.removeItem(REFRESH_KEY);
      localStorage.removeItem(USER_KEY);
    },

    isAuthenticated() {
      return Boolean(this.getToken());
    },

    isStaff() {
      const u = this.getUser();
      return Boolean(u && u.is_staff_role);
    },

    async request(path, options = {}) {
      const headers = Object.assign(
        { Accept: 'application/json' },
        options.headers || {}
      );

      const token = this.getToken();
      if (token) headers.Authorization = `Bearer ${token}`;

      let body = options.body;
      if (body && !(body instanceof FormData) && typeof body === 'object') {
        headers['Content-Type'] = 'application/json';
        body = JSON.stringify(body);
      }

      const res = await fetch(path, { ...options, headers, body });

      if (res.status === 401 && !path.includes('/api/token/')) {
        this.clearSession();
        if (!window.location.pathname.startsWith('/login')) {
          window.location.href = '/login/';
        }
        throw new Error('Session expirée');
      }

      const text = await res.text();
      let data = null;
      if (text) {
        try {
          data = JSON.parse(text);
        } catch {
          data = { detail: text };
        }
      }

      if (!res.ok) {
        const msg =
          (data && (data.detail || data.message)) ||
          (data && typeof data === 'object'
            ? Object.values(data).flat().join(' ')
            : null) ||
          `Erreur ${res.status}`;
        const err = new Error(typeof msg === 'string' ? msg : JSON.stringify(msg));
        err.status = res.status;
        err.data = data;
        throw err;
      }

      return data;
    },

    get(path, params) {
      let url = path;
      if (params) {
        const q = new URLSearchParams();
        Object.entries(params).forEach(([k, v]) => {
          if (v !== undefined && v !== null && v !== '') q.set(k, v);
        });
        const s = q.toString();
        if (s) url += (url.includes('?') ? '&' : '?') + s;
      }
      return this.request(url);
    },

    post(path, body) {
      return this.request(path, { method: 'POST', body });
    },

    put(path, body) {
      return this.request(path, { method: 'PUT', body });
    },

    patch(path, body) {
      return this.request(path, { method: 'PATCH', body });
    },

    delete(path) {
      return this.request(path, { method: 'DELETE' });
    },

    async login(username, password) {
      const data = await this.post('/api/token/', { username, password });
      return this.setSession(data);
    },

    async register(payload) {
      return this.post('/api/auth/register/', payload);
    },

    results(data) {
      if (Array.isArray(data)) return data;
      if (data && Array.isArray(data.results)) return data.results;
      return [];
    },

    count(data) {
      if (Array.isArray(data)) return data.length;
      return data && typeof data.count === 'number' ? data.count : this.results(data).length;
    },
  };

  global.Api = Api;

  global.toast = function toast(message, type) {
    const el = document.getElementById('toast');
    if (!el) return;
    el.textContent = message;
    el.classList.toggle('error', type === 'error');
    el.classList.remove('hidden');
    clearTimeout(toast._t);
    toast._t = setTimeout(() => el.classList.add('hidden'), 3200);
  };

  global.openModal = function openModal({ title, bodyHtml, onSubmit, submitLabel }) {
    const root = document.getElementById('modal-root');
    root.innerHTML = `
      <div class="modal-backdrop" id="modal-backdrop">
        <div class="modal" role="dialog" aria-modal="true">
          <div class="modal-head">
            <h3>${title}</h3>
            <button type="button" class="btn btn-ghost btn-sm" id="modal-close">✕</button>
          </div>
          <form id="modal-form">
            <div class="modal-body">${bodyHtml}</div>
            <div class="modal-foot">
              <button type="button" class="btn btn-ghost" id="modal-cancel">Annuler</button>
              <button type="submit" class="btn btn-primary">${submitLabel || 'Enregistrer'}</button>
            </div>
          </form>
        </div>
      </div>`;

    const close = () => { root.innerHTML = ''; };
    root.querySelector('#modal-close').onclick = close;
    root.querySelector('#modal-cancel').onclick = close;
    root.querySelector('#modal-backdrop').addEventListener('click', (e) => {
      if (e.target.id === 'modal-backdrop') close();
    });
    root.querySelector('#modal-form').addEventListener('submit', async (e) => {
      e.preventDefault();
      const form = e.target;
      const fd = new FormData(form);
      const payload = Object.fromEntries(fd.entries());
      try {
        await onSubmit(payload, form);
        close();
      } catch (err) {
        toast(err.message || 'Erreur', 'error');
      }
    });
  };

  global.renderPagination = function renderPagination(container, data, onPage) {
    if (!container) return;
    if (!data || !data.next && !data.previous) {
      container.innerHTML = '';
      return;
    }
    const nextUrl = data.next;
    const prevUrl = data.previous;
    container.innerHTML = `
      <button type="button" class="btn btn-ghost btn-sm" id="page-prev" ${prevUrl ? '' : 'disabled'}>Précédent</button>
      <button type="button" class="btn btn-ghost btn-sm" id="page-next" ${nextUrl ? '' : 'disabled'}>Suivant</button>
    `;
    const prev = container.querySelector('#page-prev');
    const next = container.querySelector('#page-next');
    if (prevUrl) prev.onclick = () => onPage(prevUrl);
    if (nextUrl) next.onclick = () => onPage(nextUrl);
  };

  global.statusBadge = function statusBadge(statut, estEnRetard) {
    if (estEnRetard && statut !== 'valide') {
      return '<span class="badge badge-danger">En retard</span>';
    }
    const map = {
      en_cours: ['En cours', 'badge-ok'],
      retour_en_attente: ['Validation en attente', 'badge-warn'],
      valide: ['Validé', 'badge-muted'],
    };
    const [label, cls] = map[statut] || [statut, 'badge-muted'];
    return `<span class="badge ${cls}">${label}</span>`;
  };

  global.escapeHtml = function escapeHtml(str) {
    return String(str ?? '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  };
})(window);
