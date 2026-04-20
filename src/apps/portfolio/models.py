from django.db import models
from django.utils.text import slugify


class Project(models.Model):
    # Identity — driven by GDrive folder name
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)

    # GDrive metadata — used to detect renames / re-syncs
    gdrive_folder_id = models.CharField(max_length=255, unique=True, db_index=True)
    gdrive_folder_name = models.CharField(max_length=255)

    # Content parsed from description.txt / description.md in the folder
    description = models.TextField(blank=True)
    description_html = models.TextField(blank=True, editable=False)

    # Display
    cover_image = models.ForeignKey(
        'ProjectImage',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )
    category = models.CharField(max_length=100, blank=True)
    year = models.PositiveSmallIntegerField(null=True, blank=True)
    location = models.CharField(max_length=255, blank=True)
    is_featured = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0, db_index=True)

    # Sync bookkeeping
    last_synced = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('portfolio:project_detail', kwargs={'slug': self.slug})


class ProjectImage(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='portfolio/images/')
    gdrive_file_id = models.CharField(max_length=255, unique=True, db_index=True)
    original_filename = models.CharField(max_length=255)
    caption = models.CharField(max_length=500, blank=True)
    order = models.PositiveIntegerField(default=0)
    is_cover = models.BooleanField(default=False)

    class Meta:
        ordering = ['order', 'original_filename']

    def __str__(self):
        return f'{self.project.name} — {self.original_filename}'


class ProjectDocument(models.Model):
    """Text/Markdown docs found in the GDrive folder (non-image files)."""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='documents')
    gdrive_file_id = models.CharField(max_length=255, unique=True, db_index=True)
    original_filename = models.CharField(max_length=255)
    content = models.TextField(blank=True)
    content_html = models.TextField(blank=True, editable=False)

    def __str__(self):
        return f'{self.project.name} — {self.original_filename}'
