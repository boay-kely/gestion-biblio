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
  if (menuToggle && sidebar) {
    menuToggle.addEventListener('click', () => sidebar.classList.toggle('open'));
  }

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
