import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('library', '0007_emprunt_retour_fields'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='role',
            field=models.CharField(
                choices=[
                    ('admin', 'Admin'),
                    ('bibliothecaire', 'Bibliothécaire'),
                    ('client', 'Client'),
                    ('lecteur', 'Lecteur'),
                ],
                default='client',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='membre',
            name='user',
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='membre',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name='membre',
            name='date_naissance',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='membre',
            name='lieu_naissance',
            field=models.CharField(blank=True, default='', max_length=150),
        ),
        migrations.AddField(
            model_name='emprunt',
            name='statut',
            field=models.CharField(
                choices=[
                    ('en_cours', 'En cours'),
                    ('retour_en_attente', 'Validation en attente'),
                    ('valide', 'Retour validé'),
                ],
                default='en_cours',
                max_length=30,
            ),
        ),
        # Alignement des emprunts déjà rendus
        migrations.RunPython(
            code=lambda apps, schema_editor: apps.get_model('library', 'Emprunt')
            .objects.filter(est_rendu=True)
            .update(statut='valide'),
            reverse_code=migrations.RunPython.noop,
        ),
        # Migration des anciens rôles lecteur → client (optionnel, conserve lecteur)
        migrations.RunPython(
            code=migrations.RunPython.noop,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
