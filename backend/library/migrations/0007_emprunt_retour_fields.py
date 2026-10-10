# Generated manually — champs de gestion des retours

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('library', '0006_emprunt_membre_to_membre_model'),
    ]

    operations = [
        migrations.AddField(
            model_name='emprunt',
            name='etat_retour',
            field=models.CharField(
                blank=True,
                choices=[('bon', 'Bon état'), ('abime', 'Abîmé'), ('perdu', 'Perdu')],
                max_length=20,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name='emprunt',
            name='notes_retour',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='emprunt',
            name='penalite',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
    ]
