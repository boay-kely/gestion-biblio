(function () {
  const tbody = document.getElementById('membres-tbody');
  const pagination = document.getElementById('membres-pagination');
  let currentUrl = '/api/membres/?page_size=10';

  if (!Api.isStaff()) {
    tbody.innerHTML = '<tr><td colspan="6" class="empty">Accès réservé au personnel</td></tr>';
    return;
  }

  async function load(url) {
    currentUrl = url || currentUrl;
    tbody.innerHTML = '<tr><td colspan="6" class="empty">Chargement…</td></tr>';
    try {
      const data = await Api.get(currentUrl);
      const rows = Api.results(data);
      if (!rows.length) {
        tbody.innerHTML = '<tr><td colspan="6" class="empty">Aucun membre</td></tr>';
        pagination.innerHTML = '';
        return;
      }
      tbody.innerHTML = rows
        .map((m) => {
          const date = m.date_inscription ? String(m.date_inscription).slice(0, 10) : '—';
          return `<tr>
            <td data-label="Nom">${escapeHtml(m.nom)}</td>
            <td data-label="Prénom">${escapeHtml(m.prenom)}</td>
            <td data-label="Compte">${escapeHtml(m.username || '—')}</td>
            <td data-label="Naissance">${escapeHtml(m.date_naissance || '—')}</td>
            <td data-label="Inscription">${escapeHtml(date)}</td>
            <td data-label="Actions"><div class="row-actions">
              <button type="button" class="btn btn-ghost btn-sm" data-edit="${m.id}">Modifier</button>
              <button type="button" class="btn btn-danger btn-sm" data-del="${m.id}">Supprimer</button>
            </div></td>
          </tr>`;
        })
        .join('');

      tbody.querySelectorAll('[data-edit]').forEach((btn) => {
        btn.onclick = () => openMembreModal(rows.find((r) => String(r.id) === btn.dataset.edit));
      });
      tbody.querySelectorAll('[data-del]').forEach((btn) => {
        btn.onclick = async () => {
          if (!confirm('Supprimer ce membre (et son compte) ?')) return;
          try {
            await Api.delete(`/api/membres/${btn.dataset.del}/`);
            toast('Membre supprimé');
            load();
          } catch (err) {
            toast(err.message, 'error');
          }
        };
      });

      renderPagination(pagination, data, load);
    } catch (err) {
      tbody.innerHTML = `<tr><td colspan="6" class="empty">${escapeHtml(err.message)}</td></tr>`;
    }
  }

  function openMembreModal(membre) {
    const isEdit = Boolean(membre);
    openModal({
      title: isEdit ? 'Modifier le membre' : 'Nouveau membre',
      submitLabel: isEdit ? 'Mettre à jour' : 'Créer',
      bodyHtml: `
        <div class="form-row">
          <label>Nom <input name="nom" required value="${escapeHtml(membre?.nom || '')}"></label>
          <label>Prénom <input name="prenom" required value="${escapeHtml(membre?.prenom || '')}"></label>
        </div>
        <div class="form-row">
          <label>Date de naissance <input type="date" name="date_naissance" value="${escapeHtml(membre?.date_naissance || '')}"></label>
          <label>Lieu de naissance <input name="lieu_naissance" value="${escapeHtml(membre?.lieu_naissance || '')}"></label>
        </div>
        <label>À propos <textarea name="a_propos" rows="3">${escapeHtml(membre?.a_propos || '')}</textarea></label>
      `,
      async onSubmit(payload) {
        if (!payload.date_naissance) payload.date_naissance = null;
        if (isEdit) {
          await Api.patch(`/api/membres/${membre.id}/`, payload);
          toast('Membre mis à jour');
        } else {
          await Api.post('/api/membres/', payload);
          toast('Membre créé');
        }
        load();
      },
    });
  }

  document.getElementById('btn-add-membre')?.addEventListener('click', () => openMembreModal(null));
  load();
})();
