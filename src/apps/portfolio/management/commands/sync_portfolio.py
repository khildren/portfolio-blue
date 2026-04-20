"""
Syncs the Living Portfolio from Google Drive.

GDrive folder structure expected:
  <GDRIVE_PORTFOLIO_FOLDER_ID>/
    Project Name/
      description.txt  (or description.md)
      cover.jpg        (or any image named 'cover*')
      image1.jpg
      image2.jpg
      subfolder/       (images in subfolders are included)

Run:
  python manage.py sync_portfolio
  python manage.py sync_portfolio --dry-run
  python manage.py sync_portfolio --project "Project Name"
"""
import io
import mimetypes
import os
from pathlib import Path
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.utils.text import slugify

try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseDownload
    import markdown
    HAS_GOOGLE = True
except ImportError:
    HAS_GOOGLE = False

IMAGE_MIMETYPES = {
    'image/jpeg', 'image/png', 'image/webp', 'image/gif', 'image/tiff',
}
TEXT_MIMETYPES = {
    'text/plain', 'text/markdown', 'text/x-markdown',
}
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']


def _build_service():
    creds_file = settings.GDRIVE_CREDENTIALS_FILE
    if not os.path.exists(creds_file):
        raise CommandError(
            f'Google credentials file not found: {creds_file}\n'
            'See docs/gdrive_setup.md for setup instructions.'
        )
    creds = service_account.Credentials.from_service_account_file(creds_file, scopes=SCOPES)
    return build('drive', 'v3', credentials=creds)


def _list_children(service, folder_id, page_size=200):
    """Yield all direct children of a Drive folder."""
    query = f"'{folder_id}' in parents and trashed=false"
    page_token = None
    while True:
        resp = service.files().list(
            q=query,
            pageSize=page_size,
            fields='nextPageToken, files(id, name, mimeType, modifiedTime, size)',
            pageToken=page_token,
        ).execute()
        yield from resp.get('files', [])
        page_token = resp.get('nextPageToken')
        if not page_token:
            break


def _download_file(service, file_id):
    """Download file bytes from Drive."""
    request = service.files().get_media(fileId=file_id)
    buf = io.BytesIO()
    downloader = MediaIoBaseDownload(buf, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    buf.seek(0)
    return buf.read()


def _parse_text(content_bytes, filename):
    """Return (plain_text, html) from a text/md file."""
    text = content_bytes.decode('utf-8', errors='replace')
    if filename.lower().endswith('.md'):
        try:
            html = markdown.markdown(text)
        except Exception:
            html = f'<pre>{text}</pre>'
    else:
        html = f'<p>{text.replace(chr(10), "</p><p>")}</p>'
    return text, html


class Command(BaseCommand):
    help = 'Sync Living Portfolio projects from Google Drive'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Preview changes without writing to DB or disk')
        parser.add_argument('--project', type=str, default=None, help='Only sync a specific project folder name')
        parser.add_argument('--force', action='store_true', help='Re-download all files even if already synced')

    def handle(self, *args, **options):
        if not HAS_GOOGLE:
            raise CommandError('google-api-python-client is not installed. Run: pip install google-api-python-client google-auth')

        from apps.portfolio.models import Project, ProjectImage, ProjectDocument

        dry_run = options['dry_run']
        target_name = options['project']
        force = options['force']
        folder_id = settings.GDRIVE_PORTFOLIO_FOLDER_ID

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN — no changes will be saved'))

        service = _build_service()
        self.stdout.write(f'Scanning GDrive folder {folder_id} ...')

        project_folders = [
            f for f in _list_children(service, folder_id)
            if f['mimeType'] == 'application/vnd.google-apps.folder'
        ]

        if target_name:
            project_folders = [f for f in project_folders if f['name'] == target_name]
            if not project_folders:
                raise CommandError(f'No GDrive folder named "{target_name}" found in portfolio root.')

        self.stdout.write(f'Found {len(project_folders)} project folder(s)')

        synced_gdrive_ids = set()

        for folder in project_folders:
            folder_name = folder['name']
            folder_gdrive_id = folder['id']
            synced_gdrive_ids.add(folder_gdrive_id)

            self.stdout.write(f'\n  -> {folder_name}')

            if dry_run:
                continue

            project, created = Project.objects.get_or_create(
                gdrive_folder_id=folder_gdrive_id,
                defaults={
                    'name': folder_name,
                    'gdrive_folder_name': folder_name,
                    'slug': slugify(folder_name),
                }
            )

            if not created and project.gdrive_folder_name != folder_name:
                # Folder was renamed in Drive — update display name but keep slug
                project.gdrive_folder_name = folder_name
                project.name = folder_name

            self._sync_project_contents(service, project, folder_gdrive_id, force)

            project.last_synced = timezone.now()
            project.save()

            self.stdout.write(self.style.SUCCESS(f'     OK: {project.name} ({project.images.count()} images)'))

        # Mark projects whose Drive folders are gone as inactive
        if not target_name and not dry_run:
            gone = Project.objects.exclude(gdrive_folder_id__in=synced_gdrive_ids).filter(is_active=True)
            if gone.exists():
                self.stdout.write(self.style.WARNING(f'\nDeactivating {gone.count()} project(s) no longer in Drive:'))
                for p in gone:
                    self.stdout.write(f'  - {p.name}')
                gone.update(is_active=False)

        self.stdout.write(self.style.SUCCESS('\nSync complete.'))

    def _sync_project_contents(self, service, project, folder_id, force):
        from apps.portfolio.models import ProjectImage, ProjectDocument

        children = list(_list_children(service, folder_id))
        synced_image_ids = set()
        synced_doc_ids = set()

        for item in children:
            mime = item['mimeType']
            name = item['name']
            file_id = item['id']

            # Recurse into subfolders (images only)
            if mime == 'application/vnd.google-apps.folder':
                sub_children = list(_list_children(service, file_id))
                for sub in sub_children:
                    if sub['mimeType'] in IMAGE_MIMETYPES:
                        img_id = self._sync_image(service, project, sub, force)
                        if img_id:
                            synced_image_ids.add(img_id)
                continue

            if mime in IMAGE_MIMETYPES:
                img_id = self._sync_image(service, project, item, force)
                if img_id:
                    synced_image_ids.add(img_id)

            elif mime in TEXT_MIMETYPES or name.lower().endswith(('.txt', '.md')):
                doc_id = self._sync_document(service, project, item, force)
                if doc_id:
                    synced_doc_ids.add(doc_id)

        # Remove images/docs that were deleted from Drive
        gone_images = project.images.exclude(gdrive_file_id__in=synced_image_ids)
        for img in gone_images:
            img.image.delete(save=False)
            img.delete()

        project.documents.exclude(gdrive_file_id__in=synced_doc_ids).delete()

        # Auto-set cover to first image named 'cover*' or just the first image
        if not project.cover_image_id:
            cover = project.images.filter(
                original_filename__icontains='cover'
            ).first() or project.images.first()
            if cover:
                project.cover_image = cover

    def _sync_image(self, service, project, item, force):
        from apps.portfolio.models import ProjectImage

        file_id = item['id']
        filename = item['name']

        existing = ProjectImage.objects.filter(gdrive_file_id=file_id).first()
        if existing and not force:
            return file_id

        self.stdout.write(f'     Downloading image: {filename}')
        data = _download_file(service, file_id)

        ext = Path(filename).suffix or '.jpg'
        django_filename = f'portfolio/images/{project.slug}_{file_id}{ext}'

        if existing:
            existing.image.delete(save=False)
            existing.image.save(django_filename, ContentFile(data), save=False)
            existing.original_filename = filename
            existing.save()
        else:
            img = ProjectImage(
                project=project,
                gdrive_file_id=file_id,
                original_filename=filename,
                is_cover=filename.lower().startswith('cover'),
            )
            img.image.save(django_filename, ContentFile(data), save=False)
            img.save()

        return file_id

    def _sync_document(self, service, project, item, force):
        from apps.portfolio.models import ProjectDocument
        import markdown as md_lib

        file_id = item['id']
        filename = item['name']

        existing = ProjectDocument.objects.filter(gdrive_file_id=file_id).first()
        if existing and not force:
            return file_id

        self.stdout.write(f'     Downloading doc: {filename}')
        data = _download_file(service, file_id)
        text, html = _parse_text(data, filename)

        if existing:
            existing.content = text
            existing.content_html = html
            existing.original_filename = filename
            existing.save()
        else:
            ProjectDocument.objects.create(
                project=project,
                gdrive_file_id=file_id,
                original_filename=filename,
                content=text,
                content_html=html,
            )

        # If this looks like the main description, promote it to Project.description
        if 'description' in filename.lower() or 'about' in filename.lower():
            project.description = text
            project.description_html = html

        return file_id
