# Generated manually — Emprunt.membre pointe vers library.Membre

import django.db.models.deletion
from django.db import migrations, models


def clear_incompatible_emprunts(apps, schema_editor):
    """Supprime les emprunts dont membre_id ne correspond pas à un Membre existant."""
    Emprunt = apps.get_model('library', 'Emprunt')
    Membre = apps.get_model('library', 'Membre')
    membre_ids = set(Membre.objects.values_list('id', flat=True))
    Emprunt.objects.exclude(membre_id__in=membre_ids).delete()
    # Aussi les lignes orphelines éventuelles
    Emprunt.objects.filter(membre_id__isnull=True).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('library', '0005_remove_emprunt_user'),
    ]

    operations = [
        migrations.RunPython(clear_incompatible_emprunts, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='emprunt',
            name='membre',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='emprunts',
                to='library.membre',
            ),
        ),
    ]
