(function () {
  const tbody = document.getElementById('emprunts-tbody');
  const pagination = document.getElementById('emprunts-pagination');
  let livres = [];
  let membres = [];

  function buildUrl() {
    const statut = document.getElementById('filter-statut').value;
    const params = new URLSearchParams({ page_size: '10' });
    if (statut) params.set('statut', statut);
    return `/api/emprunts/?${params}`;
  }

  async function loadRefs() {
    try {
      const livresData = await Api.get('/api/livres/', { page_size: 1000, disponible: '1' });
      livres = Api.results(livresData);
    } catch {
      livres = [];
    }
    if (Api.isStaff()) {
      try {
        const membresData = await Api.get('/api/membres/', { page_size: 1000 });
        membres = Api.results(membresData);
      } catch {
        membres = [];
      }
    }
  }

  async function load(url) {
    const endpoint = url || buildUrl();
    tbody.innerHTML = '<tr><td colspan="7" class="empty">Chargement…</td></tr>';
    try {
      const data = await Api.get(endpoint);
      const rows = Api.results(data);
      if (!rows.length) {
        tbody.innerHTML = '<tr><td colspan="7" class="empty">Aucun emprunt</td></tr>';
        pagination.innerHTML = '';
        return;
      }

      tbody.innerHTML = rows
        .map((e) => {
          const livre = e.livre_detail?.titre || `#${e.livre}`;
          const membre = e.membre_detail
            ? `${e.membre_detail.prenom} ${e.membre_detail.nom}`
            : `#${e.membre}`;
          const dateEmp = e.date_emprunt ? String(e.date_emprunt).slice(0, 10) : '—';
          let actions = '';
          if (!e.est_rendu && e.statut !== 'valide') {
            if (Api.isStaff()) {
              if (e.statut === 'retour_en_attente') {
                actions += `<button type="button" class="btn btn-primary btn-sm" data-valider="${e.id}">Valider retour</button>`;
              } else {
                actions += `<button type="button" class="btn btn-ghost btn-sm" data-retour="${e.id}">Retourner</button>`;
              }
              actions += `<button type="button" class="btn btn-danger btn-sm" data-del="${e.id}">Supprimer</button>`;
            } else if (e.statut === 'en_cours') {
              actions += `<button type="button" class="btn btn-ghost btn-sm" data-demander="${e.id}">Demander retour</button>`;
            } else if (e.statut === 'retour_en_attente') {
              actions += `<span class="badge badge-warn">En attente</span>`;
            }
          }
          return `<tr>
            <td>${escapeHtml(livre)}</td>
            <td>${escapeHtml(membre)}</td>
            <td>${escapeHtml(dateEmp)}</td>
            <td>${escapeHtml(e.date_retour_prevue || '—')}</td>
            <td>${statusBadge(e.statut, e.est_en_retard)}</td>
            <td>${escapeHtml(e.penalite_estimee || e.penalite || '0')} Ar</td>
            <td><div class="row-actions">${actions}</div></td>
          </tr>`;
        })
        .join('');

      tbody.querySelectorAll('[data-demander]').forEach((btn) => {
        btn.onclick = async () => {
          try {
            const res = await Api.post(`/api/emprunts/${btn.dataset.demander}/demander-retour/`);
            toast(res.detail || 'Demande envoyée');
            load();
          } catch (err) {
            toast(err.message, 'error');
          }
        };
      });

      tbody.querySelectorAll('[data-valider], [data-retour]').forEach((btn) => {
        btn.onclick = () => openRetourModal(btn.dataset.valider || btn.dataset.retour);
      });

      tbody.querySelectorAll('[data-del]').forEach((btn) => {
        btn.onclick = async () => {
          if (!confirm('Supprimer cet emprunt ?')) return;
          try {
            await Api.delete(`/api/emprunts/${btn.dataset.del}/`);
            toast('Emprunt supprimé');
            load();
          } catch (err) {
            toast(err.message, 'error');
          }
        };
      });

      renderPagination(pagination, data, load);
    } catch (err) {
      tbody.innerHTML = `<tr><td colspan="7" class="empty">${escapeHtml(err.message)}</td></tr>`;
    }
  }

  function openRetourModal(id) {
    openModal({
      title: 'Valider le retour',
      submitLabel: 'Valider',
      bodyHtml: `
        <label>État du livre
          <select name="etat_retour">
            <option value="bon">Bon état</option>
            <option value="abime">Abîmé</option>
            <option value="perdu">Perdu</option>
          </select>
        </label>
        <label>Date de retour <input type="date" name="date_retour" value="${new Date().toISOString().slice(0, 10)}"></label>
        <label>Notes <textarea name="notes_retour" rows="2"></textarea></label>
      `,
      async onSubmit(payload) {
        const res = await Api.post(`/api/emprunts/${id}/valider-retour/`, payload);
        toast(res.detail || 'Retour validé');
        load();
      },
    });
  }

  function openEmpruntModal() {
    const livreOpts = livres
      .map((l) => `<option value="${l.id}">${escapeHtml(l.titre)} (${l.quantite_disponible})</option>`)
      .join('');
    const membreField = Api.isStaff()
      ? `<label>Membre <select name="membre" required>${membres
          .map((m) => `<option value="${m.id}">${escapeHtml(m.prenom + ' ' + m.nom)}</option>`)
          .join('')}</select></label>`
      : '';

    const defDate = new Date();
    defDate.setDate(defDate.getDate() + 14);

    openModal({
      title: 'Nouvel emprunt',
      submitLabel: 'Emprunter',
      bodyHtml: `
        <label>Livre <select name="livre" required>${livreOpts || '<option value="">Aucun livre disponible</option>'}</select></label>
        ${membreField}
        <label>Date de retour prévue <input type="date" name="date_retour_prevue" required value="${defDate.toISOString().slice(0, 10)}"></label>
      `,
      async onSubmit(payload) {
        payload.livre = Number(payload.livre);
        if (payload.membre) payload.membre = Number(payload.membre);
        await Api.post('/api/emprunts/', payload);
        toast('Emprunt créé');
        await loadRefs();
        load();
      },
    });
  }

  document.getElementById('btn-add-emprunt')?.addEventListener('click', openEmpruntModal);
  document.getElementById('filter-statut').addEventListener('change', () => load());

  loadRefs().then(() => load());
})();
