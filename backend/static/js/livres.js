(function () {
  let currentUrl = '/api/livres/?page_size=10';
  const tbody = document.getElementById('livres-tbody');
  const pagination = document.getElementById('livres-pagination');
  let categories = [];

  async function loadCategories() {
    try {
      const data = await Api.get('/api/categories/', { page_size: 1000 });
      categories = Api.results(data);
    } catch {
      categories = [];
    }
  }

  function buildQuery() {
    const search = document.getElementById('search-livres').value.trim();
    const dispo = document.getElementById('filter-dispo').checked;
    const params = new URLSearchParams({ page_size: '10' });
    if (search) params.set('search', search);
    if (dispo) params.set('disponible', '1');
    return `/api/livres/?${params}`;
  }

  async function load(url) {
    currentUrl = url || buildQuery();
    tbody.innerHTML = '<tr><td colspan="6" class="empty">Chargement…</td></tr>';
    try {
      const data = await Api.get(currentUrl);
      const rows = Api.results(data);
      if (!rows.length) {
        tbody.innerHTML = '<tr><td colspan="6" class="empty">Aucun livre</td></tr>';
        pagination.innerHTML = '';
        return;
      }
      tbody.innerHTML = rows
        .map((l) => {
          const staffBtns = Api.isStaff()
            ? `<button type="button" class="btn btn-ghost btn-sm" data-edit="${l.id}">Modifier</button>
               <button type="button" class="btn btn-danger btn-sm" data-del="${l.id}">Supprimer</button>`
            : '';
          const pdf = l.fichier_pdf
            ? `<a class="btn btn-ghost btn-sm" href="${escapeHtml(l.fichier_pdf)}" target="_blank" rel="noopener">PDF</a>`
            : '';
          return `<tr>
            <td><strong>${escapeHtml(l.titre)}</strong></td>
            <td>${escapeHtml(l.auteur)}</td>
            <td>${escapeHtml(l.isbn)}</td>
            <td>${escapeHtml(l.categorie_nom || l.categorie)}</td>
            <td>${l.quantite_disponible}</td>
            <td><div class="row-actions">${pdf}${staffBtns}</div></td>
          </tr>`;
        })
        .join('');

      tbody.querySelectorAll('[data-edit]').forEach((btn) => {
        btn.onclick = () => openLivreModal(rows.find((r) => String(r.id) === btn.dataset.edit));
      });
      tbody.querySelectorAll('[data-del]').forEach((btn) => {
        btn.onclick = async () => {
          if (!confirm('Supprimer ce livre ?')) return;
          try {
            await Api.delete(`/api/livres/${btn.dataset.del}/`);
            toast('Livre supprimé');
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

  function categorieOptions(selected) {
    return categories
      .map(
        (c) =>
          `<option value="${c.id}" ${String(c.id) === String(selected) ? 'selected' : ''}>${escapeHtml(c.nom)}</option>`
      )
      .join('');
  }

  function openLivreModal(livre) {
    const isEdit = Boolean(livre);
    openModal({
      title: isEdit ? 'Modifier le livre' : 'Nouveau livre',
      submitLabel: isEdit ? 'Mettre à jour' : 'Créer',
      bodyHtml: `
        <label>Titre <input name="titre" required value="${escapeHtml(livre?.titre || '')}"></label>
        <label>Auteur <input name="auteur" required value="${escapeHtml(livre?.auteur || '')}"></label>
        <label>ISBN <input name="isbn" required maxlength="13" value="${escapeHtml(livre?.isbn || '')}"></label>
        <label>Catégorie <select name="categorie" required>${categorieOptions(livre?.categorie)}</select></label>
        <label>Stock <input type="number" name="quantite_disponible" min="0" value="${livre?.quantite_disponible ?? 1}"></label>
        <label>Description <textarea name="description" rows="3">${escapeHtml(livre?.description || '')}</textarea></label>
      `,
      async onSubmit(payload) {
        payload.quantite_disponible = Number(payload.quantite_disponible);
        payload.categorie = Number(payload.categorie);
        if (isEdit) {
          await Api.put(`/api/livres/${livre.id}/`, payload);
          toast('Livre mis à jour');
        } else {
          await Api.post('/api/livres/', payload);
          toast('Livre créé');
        }
        load();
      },
    });
  }

  document.getElementById('btn-add-livre')?.addEventListener('click', () => openLivreModal(null));

  let searchTimer;
  document.getElementById('search-livres').addEventListener('input', () => {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => load(), 300);
  });
  document.getElementById('filter-dispo').addEventListener('change', () => load());

  loadCategories().then(() => load());
})();
