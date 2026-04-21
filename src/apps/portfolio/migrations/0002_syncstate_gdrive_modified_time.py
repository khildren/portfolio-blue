from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('portfolio', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='SyncState',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.CharField(max_length=100, unique=True)),
                ('value', models.TextField(blank=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.AddField(
            model_name='projectimage',
            name='gdrive_modified_time',
            field=models.CharField(blank=True, max_length=40),
        ),
        migrations.AddField(
            model_name='projectdocument',
            name='gdrive_modified_time',
            field=models.CharField(blank=True, max_length=40),
        ),
    ]
