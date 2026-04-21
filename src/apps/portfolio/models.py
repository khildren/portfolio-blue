import re
from django.db import models
from django.utils.text import slugify


def _parse_folder_name(raw_name):
    """
    Parse the client's curated folder name into structured fields.

    Expected format (all fields after name are optional):
        Project Name | Category | Location | YYYY

    Examples:
        "Hillside Kitchen"
        "Hillside Kitchen | Residential"
        "Hillside Kitchen | Residential | Boulder CO | 2024"
        "Hillside Kitchen | Residential | 2024"        # location omitted
    """
    parts = [p.strip() for p in raw_name.split('|')]
    name = parts[0]
    category, location, year = '', '', None

    remaining = parts[1:]
    for part in remaining:
        if re.fullmatch(r'\d{4}', part):
            year = int(part)
        elif not category:
            category = part
        elif not location:
            location = part

    return name, category, location, year


def _image_order_key(filename):
    """
    Sort key that puts cover/hero/flyer first, then respects numeric prefixes,
    then falls back to alphabetical.
        cover.jpg  → 0
        01_front.jpg → 1
        2_side.jpg → 2
        attic.jpg  → 999 + alpha
    """
    lower = filename.lower()
    if re.match(r'^(cover|hero|flyer)[\._\- ]', lower) or lower.split('.')[0] in ('cover', 'hero', 'flyer'):
        return (0, '')
    m = re.match(r'^(\d+)[_\- ]', lower)
    if m:
        return (int(m.group(1)), lower)
    return (999, lower)


class SyncState(models.Model):
    """Stores the Drive Changes API page token so syncs are incremental."""
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.key}: {self.value[:40]}'


class Project(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)

    gdrive_folder_id = models.CharField(max_length=255, unique=True, db_index=True)
    gdrive_folder_name = models.CharField(max_length=255)

    description = models.TextField(blank=True)
    description_html = models.TextField(blank=True, editable=False)

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
            base = slugify(self.name)
            slug, n = base, 1
            while Project.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f'{base}-{n}'
                n += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('portfolio:project_detail', kwargs={'slug': self.slug})


class ProjectImage(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='portfolio/images/')
    gdrive_file_id = models.CharField(max_length=255, unique=True, db_index=True)
    gdrive_modified_time = models.CharField(max_length=40, blank=True)
    original_filename = models.CharField(max_length=255)
    caption = models.CharField(max_length=500, blank=True)
    order = models.PositiveIntegerField(default=0)
    is_cover = models.BooleanField(default=False)

    class Meta:
        ordering = ['order', 'original_filename']

    def __str__(self):
        return f'{self.project.name} — {self.original_filename}'


class ProjectDocument(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='documents')
    gdrive_file_id = models.CharField(max_length=255, unique=True, db_index=True)
    gdrive_modified_time = models.CharField(max_length=40, blank=True)
    original_filename = models.CharField(max_length=255)
    content = models.TextField(blank=True)
    content_html = models.TextField(blank=True, editable=False)

    def __str__(self):
        return f'{self.project.name} — {self.original_filename}'
