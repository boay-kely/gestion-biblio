from django.db.backends.base.base import BaseDatabaseWrapper

# Bypasser la vérification de version de la base de données (pour XAMPP / MariaDB 10.4)
BaseDatabaseWrapper.check_database_version_supported = lambda self: None