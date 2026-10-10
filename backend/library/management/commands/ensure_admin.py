"""
Crée un compte admin s'il n'existe pas encore.

Usage :
  python manage.py ensure_admin
  python manage.py ensure_admin --username admin --password secret --email a@b.c

Sur Render, variables optionnelles :
  ADMIN_USERNAME, ADMIN_PASSWORD, ADMIN_EMAIL
"""

import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Crée un superutilisateur / admin bibliothèque si absent."

    def add_arguments(self, parser):
        parser.add_argument('--username', default=os.environ.get('ADMIN_USERNAME', 'admin'))
        parser.add_argument('--password', default=os.environ.get('ADMIN_PASSWORD', ''))
        parser.add_argument('--email', default=os.environ.get('ADMIN_EMAIL', 'admin@gestion-biblio.local'))

    def handle(self, *args, **options):
        User = get_user_model()
        username = options['username']
        password = options['password'] or os.environ.get('ADMIN_PASSWORD') or 'AdminBiblio2026!'
        email = options['email']

        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.WARNING(f"L'utilisateur « {username} » existe déjà."))
            return

        user = User.objects.create_superuser(
            username=username,
            email=email,
            password=password,
        )
        user.role = 'admin'
        user.save(update_fields=['role'])
        self.stdout.write(self.style.SUCCESS(f"Admin créé : {username}"))
