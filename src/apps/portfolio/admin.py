from django.contrib import admin, messages
from django.utils.html import format_html
from .models import Project, ProjectImage, ProjectDocument, SyncState


class ProjectImageInline(admin.TabularInline):
    model = ProjectImage
    extra = 0
    readonly_fields = ('thumbnail_preview', 'gdrive_file_id', 'gdrive_modified_time', 'original_filename', 'order')
    fields = ('thumbnail_preview', 'original_filename', 'caption', 'order', 'is_cover', 'gdrive_file_id')

    def thumbnail_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" height="60" style="border-radius:4px"/>', obj.image.url)
        return '—'
    thumbnail_preview.short_description = 'Preview'


class ProjectDocumentInline(admin.TabularInline):
    model = ProjectDocument
    extra = 0
    readonly_fields = ('gdrive_file_id', 'original_filename')
    fields = ('original_filename', 'content', 'gdrive_file_id')


def _run_sync(project_name=None, full=False):
    """Run sync_portfolio programmatically from admin."""
    from django.core.management import call_command
    kwargs = {'full': full, 'dry_run': False, 'project': project_name}
    call_command('sync_portfolio', **kwargs)


@admin.action(description='↻ Sync selected projects from Google Drive')
def sync_selected(modeladmin, request, queryset):
    for project in queryset:
        try:
            _run_sync(project_name=project.gdrive_folder_name)
            messages.success(request, f'Synced: {project.name}')
        except Exception as e:
            messages.error(request, f'Error syncing {project.name}: {e}')


@admin.action(description='↻ Full sync ALL projects from Google Drive')
def sync_all(modeladmin, request, queryset):
    try:
        _run_sync(full=True)
        messages.success(request, 'Full sync complete.')
    except Exception as e:
        messages.error(request, f'Sync error: {e}')


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'year', 'location', 'is_featured', 'is_active', 'order', 'cover_thumb', 'last_synced')
    list_editable = ('order', 'is_featured', 'is_active')
    list_filter = ('is_featured', 'is_active', 'category')
    search_fields = ('name', 'description', 'location', 'gdrive_folder_name')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('gdrive_folder_id', 'gdrive_folder_name', 'description_html', 'last_synced', 'created_at', 'updated_at')
    actions = [sync_selected, sync_all]
    inlines = [ProjectImageInline, ProjectDocumentInline]

    fieldsets = (
        ('Identity', {'fields': ('name', 'slug', 'category', 'year', 'location')}),
        ('Content', {'fields': ('description', 'description_html', 'cover_image')}),
        ('Display', {'fields': ('is_featured', 'is_active', 'order')}),
        ('Google Drive', {
            'fields': ('gdrive_folder_id', 'gdrive_folder_name', 'last_synced'),
            'classes': ('collapse',),
            'description': (
                'Folder name format: <strong>Project Name | Category | Location | YYYY</strong><br>'
                'Drop an <em>info.txt</em> in the folder to override metadata without renaming.<br>'
                'Name the first/hero image <em>cover.jpg</em>, <em>hero.jpg</em>, or <em>flyer.jpg</em>.'
            ),
        }),
        ('Timestamps', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )

    def cover_thumb(self, obj):
        if obj.cover_image and obj.cover_image.image:
            return format_html('<img src="{}" height="40" style="border-radius:3px"/>', obj.cover_image.image.url)
        return '—'
    cover_thumb.short_description = 'Cover'


@admin.register(SyncState)
class SyncStateAdmin(admin.ModelAdmin):
    list_display = ('key', 'value', 'updated_at')
    readonly_fields = ('updated_at',)
