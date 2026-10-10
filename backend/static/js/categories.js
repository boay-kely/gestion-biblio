(function () {
  const tbody = document.getElementById('categories-tbody');

  if (!Api.isStaff()) {
    tbody.innerHTML = '<tr><td colspan="3" class="empty">Accès réservé au personnel</td></tr>';
    return;
  }

  async function load() {
    tbody.innerHTML = '<tr><td colspan="3" class="empty">Chargement…</td></tr>';
    try {
      const data = await Api.get('/api/categories/', { page_size: 1000 });
      const rows = Api.results(data);
      if (!rows.length) {
        tbody.innerHTML = '<tr><td colspan="3" class="empty">Aucune catégorie</td></tr>';
        return;
      }
      tbody.innerHTML = rows
        .map(
          (c) => `<tr>
            <td><strong>${escapeHtml(c.nom)}</strong></td>
            <td>${escapeHtml(c.description || '—')}</td>
            <td><div class="row-actions">
              <button type="button" class="btn btn-ghost btn-sm" data-edit="${c.id}">Modifier</button>
              <button type="button" class="btn btn-danger btn-sm" data-del="${c.id}">Supprimer</button>
            </div></td>
          </tr>`
        )
        .join('');

      tbody.querySelectorAll('[data-edit]').forEach((btn) => {
        btn.onclick = () => openCatModal(rows.find((r) => String(r.id) === btn.dataset.edit));
      });
      tbody.querySelectorAll('[data-del]').forEach((btn) => {
        btn.onclick = async () => {
          if (!confirm('Supprimer cette catégorie ?')) return;
          try {
            await Api.delete(`/api/categories/${btn.dataset.del}/`);
            toast('Catégorie supprimée');
            load();
          } catch (err) {
            toast(err.message, 'error');
          }
        };
      });
    } catch (err) {
      tbody.innerHTML = `<tr><td colspan="3" class="empty">${escapeHtml(err.message)}</td></tr>`;
    }
  }

  function openCatModal(cat) {
    const isEdit = Boolean(cat);
    openModal({
      title: isEdit ? 'Modifier la catégorie' : 'Nouvelle catégorie',
      bodyHtml: `
        <label>Nom <input name="nom" required value="${escapeHtml(cat?.nom || '')}"></label>
        <label>Description <textarea name="description" rows="3">${escapeHtml(cat?.description || '')}</textarea></label>
      `,
      async onSubmit(payload) {
        if (isEdit) {
          await Api.put(`/api/categories/${cat.id}/`, payload);
          toast('Catégorie mise à jour');
        } else {
          await Api.post('/api/categories/', payload);
          toast('Catégorie créée');
        }
        load();
      },
    });
  }

  document.getElementById('btn-add-categorie')?.addEventListener('click', () => openCatModal(null));
  load();
})();
