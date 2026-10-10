(function () {
  if (Api.isAuthenticated() && (location.pathname === '/login/' || location.pathname === '/register/')) {
    location.href = '/';
    return;
  }

  const loginForm = document.getElementById('login-form');
  if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const errEl = document.getElementById('login-error');
      errEl.classList.add('hidden');
      try {
        await Api.login(
          document.getElementById('username').value.trim(),
          document.getElementById('password').value
        );
        toast('Connexion réussie');
        location.href = '/';
      } catch (err) {
        errEl.textContent = err.message || 'Identifiants invalides';
        errEl.classList.remove('hidden');
      }
    });
  }

  const registerForm = document.getElementById('register-form');
  if (registerForm) {
    registerForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const errEl = document.getElementById('register-error');
      errEl.classList.add('hidden');
      const payload = {
        username: document.getElementById('username').value.trim(),
        password: document.getElementById('password').value,
        email: document.getElementById('email').value.trim(),
        first_name: document.getElementById('first_name').value.trim(),
        last_name: document.getElementById('last_name').value.trim(),
        date_naissance: document.getElementById('date_naissance').value || null,
        lieu_naissance: document.getElementById('lieu_naissance').value.trim(),
      };
      try {
        await Api.register(payload);
        toast('Compte créé — connectez-vous');
        location.href = '/login/';
      } catch (err) {
        errEl.textContent = err.message || 'Inscription impossible';
        errEl.classList.remove('hidden');
      }
    });
  }
})();
