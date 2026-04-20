# Google Drive Setup for Living Portfolio Sync

## 1. Create a Google Cloud Project

1. Go to https://console.cloud.google.com/
2. Create a new project: **bluesolutions-portfolio**
3. Enable the **Google Drive API** for that project

## 2. Create a Service Account

1. IAM & Admin → Service Accounts → Create Service Account
   - Name: `portfolio-sync`
   - Role: none needed (Drive read is granted via folder sharing)
2. Create a JSON key → download as `gdrive_credentials.json`
3. Copy `gdrive_credentials.json` to `/mnt/user/appdata/bluesolutions/gdrive_credentials.json`

## 3. Share Your Drive Folder

1. Open your portfolio Drive folder: https://drive.google.com/drive/folders/1g1K0dg5YFEtdna0md5PBg1-6BndfVSVk
2. Share it with the service account email (looks like `portfolio-sync@bluesolutions-portfolio.iam.gserviceaccount.com`)
3. Permission: **Viewer** is sufficient

## 4. Run the Sync

```bash
# Inside the container:
docker exec -it bluesolutions python manage.py sync_portfolio

# Preview without changes:
docker exec -it bluesolutions python manage.py sync_portfolio --dry-run

# Re-sync a single project:
docker exec -it bluesolutions python manage.py sync_portfolio --project "My Project Name"

# Force re-download all images:
docker exec -it bluesolutions python manage.py sync_portfolio --force
```

## 5. Automate with Cron (optional)

Add to your host crontab to sync nightly:
```
0 2 * * * docker exec bluesolutions python manage.py sync_portfolio >> /var/log/portfolio_sync.log 2>&1
```

## Drive Folder Structure

```
Portfolio Root/
  ├── Residential Remodel/
  │   ├── description.md        ← becomes project description (Markdown supported)
  │   ├── cover.jpg             ← auto-set as cover image (any file starting with "cover")
  │   ├── living-room.jpg
  │   ├── kitchen.jpg
  │   └── before-after/         ← subfolders are scanned for images too
  │       └── before.jpg
  ├── Commercial Office/
  │   ├── description.txt
  │   └── ...
```

**Notes:**
- Folder name = project name (can be renamed in admin after sync)
- Any `.txt` or `.md` file named `description*` or `about*` populates the project description
- Images named `cover*` are auto-set as the project cover
- Projects removed from Drive are marked inactive (not deleted)
