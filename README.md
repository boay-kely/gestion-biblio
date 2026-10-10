# Gestion Biblio

Application Django de gestion de bibliothèque : catalogue, adhérents, emprunts/retours — interface **HTML + JavaScript pur (`fetch`)** (plus de React/Node).

## Stack

- **Backend / UI** : Django 6 + DRF (API JSON) + templates Django + Vanilla JS
- **Base de données** : PostgreSQL (`dj-database-url`)
- **Prod** : Gunicorn + WhiteNoise — déployable sur **Render** sous le nom `gestion-biblio`

## Prérequis locaux

- Python 3.11+
- PostgreSQL (ou SQLite si `DATABASE_URL` est absent)

## Installation locale

```bash
cd backend
python -m venv venv
# Windows
.\venv\Scripts\activate
pip install -r requirements.txt
```

Variables d'environnement (voir `.env.example`) :

```bash
set DATABASE_URL=postgres://USER:PASSWORD@127.0.0.1:5432/bibliotheque
set DEBUG=True
```

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

- App : http://127.0.0.1:8000/
- Admin : http://127.0.0.1:8000/admin/
- API : http://127.0.0.1:8000/api/

## Déploiement Render (`gestion-biblio`)

Repo GitHub : https://github.com/boay-kely/gestion-biblio

**Blueprint (recommandé)** : https://dashboard.render.com/select-repo?type=blueprint  
→ connectez le dépôt `boay-kely/gestion-biblio` → appliquer `render.yaml`.

1. Service Web nommé **`gestion-biblio`** → URL : `https://gestion-biblio.onrender.com`
2. Build : `chmod +x build.sh && ./build.sh` — Start : `gunicorn --chdir backend core.wsgi:application`
3. Base **PostgreSQL** liée via `DATABASE_URL`
4. Variables : `SECRET_KEY`, `DEBUG=False`, `ALLOWED_HOSTS=gestion-biblio.onrender.com,gestion-biblio,.onrender.com`
5. Optionnel : `ADMIN_PASSWORD` (crée automatiquement le compte `admin` au build via `ensure_admin`)

Après le 1er déploiement, récupérez `ADMIN_PASSWORD` dans le dashboard Render (Environment) pour vous connecter.

### DNS (domaine personnalisé)

Sur le sous-domaine Render **aucune DNS** n’est requise.

Pour un domaine perso (ex. `www.votredomaine.com`) dans Render → Custom Domains :

| Type  | Nom / Host | Valeur / Target                 | TTL  |
|-------|------------|---------------------------------|------|
| CNAME | `www`      | `gestion-biblio.onrender.com`   | 3600 |
| CNAME | `@`*       | `gestion-biblio.onrender.com`   | 3600 |

\* Si le registrar n’accepte pas CNAME sur `@`, utilisez les enregistrements **A/AAAA** fournis par Render, ou une redirection apex → `www`.

Puis ajoutez le domaine dans `ALLOWED_HOSTS` et `CSRF_TRUSTED_ORIGINS`.

## Modules

| Module     | Description                                      |
|------------|--------------------------------------------------|
| Auth       | JWT, inscription client, rôles staff / client    |
| Livres     | CRUD catalogue + stock                           |
| Catégories | CRUD (staff)                                     |
| Membres    | Fiches adhérents (staff)                         |
| Emprunts   | Prêt, demande de retour, validation, pénalités   |
