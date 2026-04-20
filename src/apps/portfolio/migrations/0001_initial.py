from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Project',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('slug', models.SlugField(blank=True, max_length=255, unique=True)),
                ('gdrive_folder_id', models.CharField(db_index=True, max_length=255, unique=True)),
                ('gdrive_folder_name', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True)),
                ('description_html', models.TextField(blank=True, editable=False)),
                ('category', models.CharField(blank=True, max_length=100)),
                ('year', models.PositiveSmallIntegerField(blank=True, null=True)),
                ('location', models.CharField(blank=True, max_length=255)),
                ('is_featured', models.BooleanField(default=False)),
                ('order', models.PositiveIntegerField(db_index=True, default=0)),
                ('last_synced', models.DateTimeField(blank=True, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={'ordering': ['order', 'name']},
        ),
        migrations.CreateModel(
            name='ProjectImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='portfolio/images/')),
                ('gdrive_file_id', models.CharField(db_index=True, max_length=255, unique=True)),
                ('original_filename', models.CharField(max_length=255)),
                ('caption', models.CharField(blank=True, max_length=500)),
                ('order', models.PositiveIntegerField(default=0)),
                ('is_cover', models.BooleanField(default=False)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='images', to='portfolio.project')),
            ],
            options={'ordering': ['order', 'original_filename']},
        ),
        migrations.CreateModel(
            name='ProjectDocument',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('gdrive_file_id', models.CharField(db_index=True, max_length=255, unique=True)),
                ('original_filename', models.CharField(max_length=255)),
                ('content', models.TextField(blank=True)),
                ('content_html', models.TextField(blank=True, editable=False)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='documents', to='portfolio.project')),
            ],
        ),
        migrations.AddField(
            model_name='project',
            name='cover_image',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='portfolio.projectimage'),
        ),
    ]
