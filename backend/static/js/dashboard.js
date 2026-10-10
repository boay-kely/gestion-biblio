(async function () {
  const tbody = document.getElementById('recent-emprunts');

  try {
    const [livres, emprunts, alertes] = await Promise.all([
      Api.get('/api/livres/', { page_size: 1 }),
      Api.get('/api/emprunts/', { page_size: 5 }),
      Api.get('/api/emprunts/alertes/'),
    ]);

    document.getElementById('stat-livres').textContent = Api.count(livres);
    document.getElementById('stat-emprunts').textContent = Api.results(emprunts).filter(
      (e) => !e.est_rendu && e.statut !== 'valide'
    ).length;
    document.getElementById('stat-retards').textContent = (alertes || []).length;

    if (Api.isStaff()) {
      const membres = await Api.get('/api/membres/', { page_size: 1 });
      document.getElementById('stat-membres').textContent = Api.count(membres);
    }

    const rows = Api.results(emprunts);
    if (!rows.length) {
      tbody.innerHTML = '<tr><td colspan="4" class="empty">Aucun emprunt</td></tr>';
      return;
    }

    tbody.innerHTML = rows
      .map((e) => {
        const livre = e.livre_detail?.titre || `#${e.livre}`;
        const membre = e.membre_detail
          ? `${e.membre_detail.prenom} ${e.membre_detail.nom}`
          : `#${e.membre}`;
        return `<tr>
          <td data-label="Livre">${escapeHtml(livre)}</td>
          <td data-label="Membre">${escapeHtml(membre)}</td>
          <td data-label="Retour prévu">${escapeHtml(e.date_retour_prevue || '—')}</td>
          <td data-label="Statut">${statusBadge(e.statut, e.est_en_retard)}</td>
        </tr>`;
      })
      .join('');
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="4" class="empty">${escapeHtml(err.message)}</td></tr>`;
  }
})();
