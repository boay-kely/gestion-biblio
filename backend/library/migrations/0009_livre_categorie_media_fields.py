from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('library', '0008_client_workflow'),
    ]

    operations = [
        migrations.AddField(
            model_name='categorie',
            name='description',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='livre',
            name='description',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='livre',
            name='fichier_pdf',
            field=models.FileField(blank=True, null=True, upload_to='livres/pdfs/'),
        ),
    ]
