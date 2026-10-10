(function () {
  const publicPages = ['/login/', '/register/'];
  if (!publicPages.includes(location.pathname) && !Api.isAuthenticated()) {
    location.href = '/login/';
    return;
  }

  const user = Api.getUser();
  if (user) {
    const nameEl = document.getElementById('user-name');
    const roleEl = document.getElementById('user-role');
    if (nameEl) nameEl.textContent = user.username;
    if (roleEl) roleEl.textContent = user.role || '';
  }

  document.querySelectorAll('.staff-only').forEach((el) => {
    if (!Api.isStaff()) el.classList.add('hidden-role');
  });

  const logoutBtn = document.getElementById('btn-logout');
  if (logoutBtn) {
    logoutBtn.addEventListener('click', () => {
      Api.clearSession();
      location.href = '/login/';
    });
  }

  const menuToggle = document.getElementById('menu-toggle');
  const sidebar = document.getElementById('sidebar');
  const backdrop = document.getElementById('sidebar-backdrop');

  function setMenuOpen(open) {
    if (!sidebar) return;
    sidebar.classList.toggle('open', open);
    sidebar.setAttribute('aria-hidden', open ? 'false' : 'true');
    document.body.style.overflow = open ? 'hidden' : '';
    if (menuToggle) {
      menuToggle.setAttribute('aria-expanded', open ? 'true' : 'false');
      menuToggle.setAttribute('aria-label', open ? 'Fermer le menu' : 'Ouvrir le menu');
    }
    if (backdrop) {
      backdrop.hidden = !open;
      backdrop.classList.toggle('visible', open);
    }
  }

  if (menuToggle && sidebar) {
    menuToggle.addEventListener('click', () => {
      setMenuOpen(!sidebar.classList.contains('open'));
    });
  }

  if (backdrop) {
    backdrop.addEventListener('click', () => setMenuOpen(false));
  }

  if (sidebar) {
    sidebar.querySelectorAll('.nav-link').forEach((link) => {
      link.addEventListener('click', () => setMenuOpen(false));
    });
  }

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') setMenuOpen(false);
  });

  window.addEventListener('resize', () => {
    if (window.innerWidth > 800) setMenuOpen(false);
  });

  async function loadAlertes() {
    const banner = document.getElementById('alertes-banner');
    if (!banner || !Api.isAuthenticated()) return;
    try {
      const alertes = await Api.get('/api/emprunts/alertes/');
      if (!alertes || !alertes.length) {
        banner.classList.add('hidden');
        return;
      }
      banner.textContent = alertes[0].message + (alertes.length > 1 ? ` (+${alertes.length - 1})` : '');
      banner.classList.remove('hidden');
    } catch {
      banner.classList.add('hidden');
    }
  }

  loadAlertes();
})();
