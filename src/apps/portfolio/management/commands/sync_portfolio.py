"""
Living Portfolio — Google Drive sync command.

Client workflow:
  1. Create a folder inside the portfolio root Drive folder
  2. Name it using the format:  Project Name | Category | Location | YYYY
     (only Project Name is required; extras are optional)
  3. Drop images in — first image named cover/hero/flyer becomes the hero
  4. Optionally add description.txt / description.md for copy
  5. Optionally add info.txt for structured overrides (see below)

info.txt format (plain key: value, all optional):
  featured: yes
  category: Residential
  location: Denver, CO
  year: 2025
  description: One-line override for the project blurb.

Image ordering:
  cover.jpg / hero.jpg / flyer.jpg  →  hero (order 0)
  01_front.jpg / 1_side.jpg         →  respects numeric prefix
  anything else                      →  alphabetical after above

Sync modes:
  --full        Re-download everything regardless of Drive modified time
  --project X   Only sync the folder named X (full re-download)
  --dry-run     Print what would change, touch nothing

Incremental (default):
  Uses the Drive Changes API pageToken stored in DB.
  Only folders with activity since last sync are re-examined.
  New installs do a full scan on first run to build the token.

Run:
  python manage.py sync_portfolio
  python manage.py sync_portfolio --dry-run
  python manage.py sync_portfolio --full
  python manage.py sync_portfolio --project "Hillside Kitchen"
"""

import io
import json
import os
import re
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

try:
    import pillow_heif
    pillow_heif.register_heif_opener()
    HAS_HEIF = True
except ImportError:
    HAS_HEIF = False

IMAGE_MIMETYPES = {
    'image/jpeg', 'image/png', 'image/webp', 'image/gif', 'image/tiff',
    'image/heic', 'image/heif',  # iOS / iPhone photos
}
TEXT_MIMETYPES = {'text/plain', 'text/markdown', 'text/x-markdown'}
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
PAGE_TOKEN_KEY = 'gdrive_changes_page_token'


# ── Drive helpers ────────────────────────────────────────────────────────────

def _build_service():
    creds_file = settings.GDRIVE_CREDENTIALS_FILE
    if not os.path.exists(creds_file):
        raise CommandError(
            f'Credentials file not found: {creds_file}\n'
            'See docs/gdrive_setup.md for setup instructions.'
        )
    creds = service_account.Credentials.from_service_account_file(creds_file, scopes=SCOPES)
    return build('drive', 'v3', credentials=creds, cache_discovery=False)


def _list_children(service, folder_id):
    items = []
    token = None
    while True:
        resp = service.files().list(
            q=f"'{folder_id}' in parents and trashed=false",
            pageSize=200,
            fields='nextPageToken, files(id, name, mimeType, modifiedTime, size)',
            pageToken=token,
        ).execute()
        items.extend(resp.get('files', []))
        token = resp.get('nextPageToken')
        if not token:
            break
    return items


def _maybe_convert_heic(data, filename):
    """Convert HEIC/HEIF bytes to JPEG. Returns (data, filename)."""
    ext = Path(filename).suffix.lower()
    if ext not in ('.heic', '.heif'):
        return data, filename
    if not HAS_HEIF:
        return data, filename
    from PIL import Image
    img = Image.open(io.BytesIO(data))
    buf = io.BytesIO()
    img.convert('RGB').save(buf, format='JPEG', quality=90)
    buf.seek(0)
    new_name = Path(filename).stem + '.jpg'
    return buf.read(), new_name


def _collect_images(service, folder_id, subfolder_label=None):
    """Recursively collect all images under folder_id.
    Returns list of (item, subfolder_label) tuples."""
    results = []
    for item in _list_children(service, folder_id):
        mime = item['mimeType']
        if mime == 'application/vnd.google-apps.folder':
            label = subfolder_label or item['name']
            results.extend(_collect_images(service, item['id'], label))
        elif mime in IMAGE_MIMETYPES:
            results.append((item, subfolder_label))
    return results


def _download(service, file_id):
    req = service.files().get_media(fileId=file_id)
    buf = io.BytesIO()
    dl = MediaIoBaseDownload(buf, req)
    done = False
    while not done:
        _, done = dl.next_chunk()
    buf.seek(0)
    return buf.read()


def _get_start_token(service):
    resp = service.changes().getStartPageToken().execute()
    return resp['startPageToken']


def _get_changed_folder_ids(service, page_token, root_folder_id):
    """Return set of folder IDs that had any Drive activity since page_token."""
    changed_ids = set()
    token = page_token
    new_token = token
    while True:
        resp = service.changes().list(
            pageToken=token,
            spaces='drive',
            fields='nextPageToken, newStartPageToken, changes(fileId, file(parents, mimeType, trashed))',
            includeRemoved=True,
        ).execute()
        for change in resp.get('changes', []):
            f = change.get('file') or {}
            parents = f.get('parents', [])
            # We care about any file whose parent is the root folder,
            # or any subfolder inside a project folder (image added/removed).
            # Simplest: return the parent folder IDs that are direct children
            # of root, then the caller decides whether to re-sync that project.
            changed_ids.add(change['fileId'])
            changed_ids.update(parents)
        new_token = resp.get('newStartPageToken', new_token)
        token = resp.get('nextPageToken')
        if not token:
            break
    return changed_ids, new_token


# ── Metadata helpers ─────────────────────────────────────────────────────────

def _parse_info_txt(text):
    """Parse a simple key: value info.txt into a dict."""
    result = {}
    for line in text.splitlines():
        if ':' in line:
            k, _, v = line.partition(':')
            result[k.strip().lower()] = v.strip()
    return result


def _parse_text(data, filename):
    text = data.decode('utf-8', errors='replace')
    if filename.lower().endswith('.md'):
        try:
            html = markdown.markdown(text)
        except Exception:
            html = f'<pre>{text}</pre>'
    else:
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        html = ''.join(f'<p>{p.replace(chr(10), " ")}</p>' for p in paragraphs) or f'<p>{text}</p>'
    return text, html


def _image_order(filename):
    lower = filename.lower()
    stem = Path(lower).stem
    if stem in ('cover', 'hero', 'flyer') or re.match(r'^(cover|hero|flyer)[\._\- ]', lower):
        return (0, lower)
    m = re.match(r'^(\d+)[_\- ]', lower)
    if m:
        return (int(m.group(1)), lower)
    return (999, lower)


def _is_cover_filename(filename):
    stem = Path(filename.lower()).stem
    return stem in ('cover', 'hero', 'flyer') or bool(
        re.match(r'^(cover|hero|flyer)[\._\- ]', filename.lower())
    )


# ── Main command ─────────────────────────────────────────────────────────────

class Command(BaseCommand):
    help = 'Sync Living Portfolio from Google Drive (incremental by default)'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true')
        parser.add_argument('--full', action='store_true', help='Re-download all files')
        parser.add_argument('--project', type=str, default=None, help='Sync one folder by name')

    def handle(self, *args, **options):
        if not HAS_GOOGLE:
            raise CommandError('Run: pip install google-api-python-client google-auth markdown')

        from apps.portfolio.models import Project, ProjectImage, ProjectDocument, SyncState
        from apps.portfolio.models import _parse_folder_name

        dry_run = options['dry_run']
        full = options['full']
        target = options['project']
        root_id = settings.GDRIVE_PORTFOLIO_FOLDER_ID

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN — no writes'))

        service = _build_service()

        # ── Determine which project folders need syncing ──────────────────
        all_folders = [
            f for f in _list_children(service, root_id)
            if f['mimeType'] == 'application/vnd.google-apps.folder'
        ]

        if target:
            to_sync = [f for f in all_folders if f['name'] == target]
            if not to_sync:
                raise CommandError(f'No folder named "{target}" in portfolio root.')
            changed_folder_ids = {f['id'] for f in to_sync}
            new_page_token = None
        elif full:
            to_sync = all_folders
            changed_folder_ids = {f['id'] for f in all_folders}
            new_page_token = None
        else:
            # Incremental — use Changes API
            state, _ = SyncState.objects.get_or_create(key=PAGE_TOKEN_KEY)
            if not state.value:
                # First run: full scan, then store token
                self.stdout.write('First run — full scan to initialise change token.')
                to_sync = all_folders
                changed_folder_ids = {f['id'] for f in all_folders}
                new_page_token = _get_start_token(service)
            else:
                changed_ids, new_page_token = _get_changed_folder_ids(
                    service, state.value, root_id
                )
                to_sync = [f for f in all_folders if f['id'] in changed_ids
                           or any(f['id'] == cid for cid in changed_ids)]
                # Also catch new folders (their parent = root_id is in changed_ids)
                if root_id in changed_ids:
                    to_sync = all_folders  # root changed → rescan all
                changed_folder_ids = changed_ids

        self.stdout.write(
            f'Portfolio root: {root_id}\n'
            f'Total folders in root: {len(all_folders)}\n'
            f'Folders to sync: {len(to_sync)}'
        )

        synced_gdrive_ids = {f['id'] for f in all_folders}  # all live folders

        for folder in to_sync:
            folder_name = folder['name']
            folder_id = folder['id']

            parsed_name, parsed_cat, parsed_loc, parsed_year = _parse_folder_name(folder_name)
            self.stdout.write(f'\n  → {folder_name}')
            if dry_run:
                self.stdout.write(f'     name={parsed_name} cat={parsed_cat} loc={parsed_loc} year={parsed_year}')
                continue

            project, created = Project.objects.get_or_create(
                gdrive_folder_id=folder_id,
                defaults={
                    'name': parsed_name,
                    'gdrive_folder_name': folder_name,
                    'slug': slugify(parsed_name),
                    'category': parsed_cat,
                    'location': parsed_loc,
                    'year': parsed_year,
                }
            )

            # On rename: update parsed fields
            if not created and project.gdrive_folder_name != folder_name:
                project.gdrive_folder_name = folder_name
                project.name = parsed_name
                if parsed_cat:
                    project.category = parsed_cat
                if parsed_loc:
                    project.location = parsed_loc
                if parsed_year:
                    project.year = parsed_year

            self._sync_contents(service, project, folder_id, full, created)

            project.last_synced = timezone.now()
            project.is_active = True
            project.save()

            self.stdout.write(self.style.SUCCESS(
                f'     ✓ {project.name}  [{project.images.count()} images]'
            ))

        # Deactivate projects whose Drive folders were deleted
        if not target and not dry_run:
            gone = Project.objects.exclude(gdrive_folder_id__in=synced_gdrive_ids).filter(is_active=True)
            for p in gone:
                p.is_active = False
                p.save()
                self.stdout.write(self.style.WARNING(f'  ✗ Deactivated: {p.name}'))

        # Save new page token
        if not dry_run and new_page_token:
            state, _ = SyncState.objects.get_or_create(key=PAGE_TOKEN_KEY)
            state.value = new_page_token
            state.save()

        self.stdout.write(self.style.SUCCESS('\nSync complete.'))

    # ── Folder content sync ───────────────────────────────────────────────

    def _sync_contents(self, service, project, folder_id, force, is_new):
        from apps.portfolio.models import ProjectImage, ProjectDocument
        from apps.portfolio.models import _parse_folder_name

        children = _list_children(service, folder_id)
        synced_img_ids, synced_doc_ids = set(), set()
        info_overrides = {}
        pending_images = []  # (item, subfolder_name_or_None)
        pending_docs = []

        # First pass — collect info.txt / description files, queue images
        for item in children:
            mime = item['mimeType']
            name = item['name']

            if mime == 'application/vnd.google-apps.folder':
                pending_images.extend(_collect_images(service, item['id'], name))
                continue

            if name.lower() in ('info.txt', 'info.json'):
                data = _download(service, item['id'])
                if name.lower().endswith('.json'):
                    try:
                        info_overrides = json.loads(data.decode('utf-8', errors='replace'))
                    except Exception:
                        pass
                else:
                    info_overrides = _parse_info_txt(data.decode('utf-8', errors='replace'))
                continue

            if mime in IMAGE_MIMETYPES:
                pending_images.append((item, None))
            elif mime in TEXT_MIMETYPES or name.lower().endswith(('.txt', '.md')):
                pending_docs.append(item)

        # Apply info.txt overrides (only if set — don't blank existing admin edits)
        changed = False
        if 'category' in info_overrides and info_overrides['category']:
            project.category = info_overrides['category']; changed = True
        if 'location' in info_overrides and info_overrides['location']:
            project.location = info_overrides['location']; changed = True
        if 'year' in info_overrides and info_overrides['year']:
            try:
                project.year = int(str(info_overrides['year'])[:4]); changed = True
            except (ValueError, TypeError):
                pass
        if 'featured' in info_overrides:
            project.is_featured = str(info_overrides['featured']).lower() in ('yes', 'true', '1')
            changed = True
        if 'description' in info_overrides and info_overrides['description']:
            project.description = info_overrides['description']
            project.description_html = f'<p>{info_overrides["description"]}</p>'
            changed = True

        # Sort images by our cover/numeric/alpha order
        pending_images.sort(key=lambda t: _image_order(t[0]['name']))

        # Sync images
        for order_idx, (item, subfolder) in enumerate(pending_images):
            file_id = item['id']
            mod_time = item.get('modifiedTime', '')
            existing = ProjectImage.objects.filter(gdrive_file_id=file_id).first()

            # Skip download if unchanged (unless force)
            if existing and not force and existing.gdrive_modified_time == mod_time:
                synced_img_ids.add(file_id)
                continue

            caption = subfolder.replace('_', ' ').replace('-', ' ').title() if subfolder else ''
            is_cover = _is_cover_filename(item['name']) or (order_idx == 0 and not existing)

            self.stdout.write(f'     ↓ {item["name"]}')
            data = _download(service, file_id)
            data, saved_name = _maybe_convert_heic(data, item['name'])
            ext = Path(saved_name).suffix or '.jpg'
            django_path = f'{project.slug}_{file_id}{ext}'

            if existing:
                existing.image.delete(save=False)
                existing.image.save(django_path, ContentFile(data), save=False)
                existing.original_filename = item['name']
                existing.gdrive_modified_time = mod_time
                existing.order = order_idx
                existing.caption = caption or existing.caption
                existing.is_cover = is_cover
                existing.save()
            else:
                img = ProjectImage(
                    project=project,
                    gdrive_file_id=file_id,
                    original_filename=item['name'],
                    gdrive_modified_time=mod_time,
                    order=order_idx,
                    caption=caption,
                    is_cover=is_cover,
                )
                img.image.save(django_path, ContentFile(data), save=False)
                img.save()

            synced_img_ids.add(file_id)

        # Auto-assign cover: prefer is_cover flag, then order=0
        if not project.cover_image_id or not ProjectImage.objects.filter(
            pk=project.cover_image_id
        ).exists():
            cover = (
                project.images.filter(is_cover=True).first()
                or project.images.order_by('order').first()
            )
            if cover:
                project.cover_image = cover
                changed = True

        # Sync text documents
        for item in pending_docs:
            file_id = item['id']
            mod_time = item.get('modifiedTime', '')
            existing = ProjectDocument.objects.filter(gdrive_file_id=file_id).first()

            if existing and not force and existing.gdrive_modified_time == mod_time:
                synced_doc_ids.add(file_id)
                continue

            self.stdout.write(f'     ↓ {item["name"]}')
            data = _download(service, file_id)
            text, html = _parse_text(data, item['name'])
            name_lower = item['name'].lower()

            # Promote to project description if it looks like the main copy
            if any(k in name_lower for k in ('description', 'about', 'overview')):
                if not info_overrides.get('description'):  # don't override info.txt
                    project.description = text
                    project.description_html = html
                    changed = True

            if existing:
                existing.content = text
                existing.content_html = html
                existing.gdrive_modified_time = mod_time
                existing.original_filename = item['name']
                existing.save()
            else:
                ProjectDocument.objects.create(
                    project=project,
                    gdrive_file_id=file_id,
                    original_filename=item['name'],
                    gdrive_modified_time=mod_time,
                    content=text,
                    content_html=html,
                )
            synced_doc_ids.add(file_id)

        # Remove files deleted from Drive
        gone_imgs = project.images.exclude(gdrive_file_id__in=synced_img_ids)
        for img in gone_imgs:
            img.image.delete(save=False)
            img.delete()
        project.documents.exclude(gdrive_file_id__in=synced_doc_ids).delete()

        if changed:
            project.save(update_fields=[
                'category', 'location', 'year', 'is_featured',
                'description', 'description_html', 'cover_image',
            ])
