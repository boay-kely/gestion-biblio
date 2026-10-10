# DNS — domaine `gestion-biblio` (Render)

## Option A — Sous-domaine Render (recommandé, sans DNS)

| Élément        | Valeur                                      |
|----------------|---------------------------------------------|
| Nom du service | `gestion-biblio`                            |
| URL            | `https://gestion-biblio.onrender.com`       |
| DNS à créer    | **Aucun** (fourni par Render)               |

`ALLOWED_HOSTS` contient déjà `gestion-biblio.onrender.com` et `gestion-biblio`.

---

## Option B — Domaine personnalisé

Dans Render → votre service **gestion-biblio** → **Settings** → **Custom Domains** → ajoutez votre domaine, puis chez votre registrar :

### Enregistrements DNS à créer

```
# Sous-domaine www
Type:  CNAME
Host:  www
Value: gestion-biblio.onrender.com
TTL:   3600

# Apex / racine (si CNAME apex autorisé ; sinon voir A/AAAA Render)
Type:  CNAME
Host:  @
Value: gestion-biblio.onrender.com
TTL:   3600
```

### Tableau récapitulatif

| Type  | Nom (Host) | Valeur / Target               | TTL  |
|-------|------------|-------------------------------|------|
| CNAME | `www`      | `gestion-biblio.onrender.com` | 3600 |
| CNAME | `@`        | `gestion-biblio.onrender.com` | 3600 |

Si le registrar refuse un CNAME sur `@`, utilisez les enregistrements **A** / **AAAA** affichés dans le dashboard Render pour ce domaine, ou redirigez l’apex vers `www`.

Après validation DNS, ajoutez dans les variables d’environnement Render :

```
ALLOWED_HOSTS=gestion-biblio.onrender.com,gestion-biblio,www.votredomaine.com,votredomaine.com
CSRF_TRUSTED_ORIGINS=https://gestion-biblio.onrender.com,https://www.votredomaine.com,https://votredomaine.com
```
