from decimal import Decimal

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


PENALITE_PAR_JOUR = Decimal('500')


class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('bibliothecaire', 'Bibliothécaire'),
        ('client', 'Client'),
        ('lecteur', 'Lecteur'),  # alias historique = client
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='client')

    def __str__(self):
        return f"{self.username} ({self.role})"

    @property
    def is_staff_role(self):
        return self.role in ('admin', 'bibliothecaire') or self.is_superuser

    @property
    def is_client_role(self):
        return self.role in ('client', 'lecteur')


class Categorie(models.Model):
    nom = models.CharField(max_length=100)
    description = models.TextField(blank=True, default='')

    def __str__(self):
        return self.nom


class Livre(models.Model):
    titre = models.CharField(max_length=200)
    auteur = models.CharField(max_length=150)
    isbn = models.CharField(max_length=13, unique=True)
    description = models.TextField(blank=True, default='')
    quantite_disponible = models.IntegerField(default=1)
    categorie = models.ForeignKey(Categorie, on_delete=models.CASCADE, related_name='livres')
    fichier_pdf = models.FileField(upload_to='livres/pdfs/', blank=True, null=True)

    def __str__(self):
        return self.titre


class Membre(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='membre',
        null=True,
        blank=True,
    )
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    date_naissance = models.DateField(null=True, blank=True)
    lieu_naissance = models.CharField(max_length=150, blank=True, default='')
    a_propos = models.TextField(blank=True, null=True)
    date_inscription = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nom} {self.prenom}"


class Emprunt(models.Model):
    ETAT_RETOUR_CHOICES = (
        ('bon', 'Bon état'),
        ('abime', 'Abîmé'),
        ('perdu', 'Perdu'),
    )
    STATUT_CHOICES = (
        ('en_cours', 'En cours'),
        ('retour_en_attente', 'Validation en attente'),
        ('valide', 'Retour validé'),
    )

    membre = models.ForeignKey(Membre, on_delete=models.CASCADE, related_name='emprunts')
    livre = models.ForeignKey(Livre, on_delete=models.CASCADE, related_name='emprunts')
    date_emprunt = models.DateTimeField(auto_now_add=True)
    date_retour_prevue = models.DateField()
    date_retour_effective = models.DateTimeField(null=True, blank=True)
    est_rendu = models.BooleanField(default=False)
    statut = models.CharField(
        max_length=30,
        choices=STATUT_CHOICES,
        default='en_cours',
    )
    etat_retour = models.CharField(
        max_length=20,
        choices=ETAT_RETOUR_CHOICES,
        null=True,
        blank=True,
    )
    notes_retour = models.TextField(blank=True, null=True)
    penalite = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.membre} - {self.livre.titre}"

    @property
    def est_actif(self):
        return not self.est_rendu and self.statut != 'valide'

    @property
    def est_en_retard(self):
        if not self.est_actif or not self.date_retour_prevue:
            return False
        return timezone.localdate() > self.date_retour_prevue

    def jours_de_retard(self, as_of=None):
        if not self.date_retour_prevue:
            return 0
        ref = as_of or timezone.localdate()
        if ref <= self.date_retour_prevue:
            return 0
        return (ref - self.date_retour_prevue).days

    def calculer_penalite(self, as_of=None):
        return PENALITE_PAR_JOUR * self.jours_de_retard(as_of)
