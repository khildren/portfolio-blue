from django.contrib import admin
from django.utils.html import format_html
from .models import Project, ProjectImage, ProjectDocument


class ProjectImageInline(admin.TabularInline):
    model = ProjectImage
    extra = 0
    readonly_fields = ('gdrive_file_id', 'thumbnail_preview', 'original_filename')
    fields = ('thumbnail_preview', 'original_filename', 'caption', 'order', 'is_cover', 'gdrive_file_id')

    def thumbnail_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" height="60" />', obj.image.url)
        return '—'
    thumbnail_preview.short_description = 'Preview'


class ProjectDocumentInline(admin.TabularInline):
    model = ProjectDocument
    extra = 0
    readonly_fields = ('gdrive_file_id', 'original_filename', 'content')
    fields = ('original_filename', 'content', 'gdrive_file_id')


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'year', 'location', 'is_featured', 'is_active', 'order', 'last_synced')
    list_editable = ('order', 'is_featured', 'is_active')
    list_filter = ('is_featured', 'is_active', 'category')
    search_fields = ('name', 'description', 'location')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('gdrive_folder_id', 'gdrive_folder_name', 'description_html', 'last_synced', 'created_at', 'updated_at')
    inlines = [ProjectImageInline, ProjectDocumentInline]

    fieldsets = (
        ('Identity', {
            'fields': ('name', 'slug', 'category', 'year', 'location')
        }),
        ('Content', {
            'fields': ('description', 'description_html', 'cover_image')
        }),
        ('Display', {
            'fields': ('is_featured', 'is_active', 'order')
        }),
        ('Google Drive', {
            'fields': ('gdrive_folder_id', 'gdrive_folder_name', 'last_synced'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
