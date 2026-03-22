import requests
import os
import asyncio
from pathlib import Path
import logging
import shutil

# --- Configuration ---
REPO_OWNER = "jj-sm"
REPO_NAME = "airac"
DB_ASSET_NAME = "airac.s3db"
DATA_DIR = Path("./data")
DB_PATH = DATA_DIR / DB_ASSET_NAME
VERSION_FILE = DATA_DIR / "airac_version.txt"
CHECK_INTERVAL_SECONDS = 12 * 60 * 60  # 12 hours
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")  # <-- Added

# --- Logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def get_latest_release_info():
    """Fetches the latest release information from the GitHub API."""
    api_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/latest"
    headers = {"Accept": "application/vnd.github.v3+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"

    try:
        logger.info(f"Checking for new releases at {api_url}")
        response = requests.get(api_url, headers=headers, timeout=15)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        if e.response and e.response.status_code == 404:
            logger.error(
                f"Repository or release not found at {api_url}. Please check repo name and ensure token has 'repo' scope.")
        else:
            logger.error(f"Failed to fetch latest release info: {e}")
        return None


def get_current_version():
    """Reads the current downloaded version from the version file."""
    try:
        if VERSION_FILE.exists():
            return VERSION_FILE.read_text().strip()
    except IOError as e:
        logger.error(f"Could not read version file: {e}")
    return None


def update_current_version(version_tag: str):
    """Writes the new version tag to the version file."""
    try:
        DATA_DIR.mkdir(exist_ok=True)
        VERSION_FILE.write_text(version_tag)
    except IOError as e:
        logger.error(f"Could not write to version file: {e}")


def download_db_asset(asset_url: str):
    """Downloads the database asset to a temporary file and replaces the current one."""
    temp_db_path = DB_PATH.with_suffix(".s3db.tmp")
    headers = {"Accept": "application/octet-stream"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"

    try:
        logger.info(f"Downloading new database from {asset_url}...")
        with requests.get(asset_url, headers=headers, stream=True,
                          timeout=300) as r:  # 5-minute timeout
            r.raise_for_status()
            with open(temp_db_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

        logger.info("Download complete. Replacing database file.")
        shutil.move(temp_db_path, DB_PATH)
        logger.info(f"Database updated successfully to {DB_PATH}")
        return True

    except (requests.RequestException, IOError, OSError) as e:
        logger.error(f"Failed to download or replace database: {e}")
        if temp_db_path.exists():
            os.remove(temp_db_path)  # Clean up temp file
        return False


async def check_and_update_db():
    """The main function to check for updates and trigger download if needed."""
    release_info = get_latest_release_info()
    if not release_info:
        return

    latest_version_tag = release_info.get("tag_name")
    if not latest_version_tag:
        logger.warning("Could not find 'tag_name' in release info.")
        return

    current_version = get_current_version()
    logger.info(
        f"Latest release version: {latest_version_tag}, Current local version: {current_version}")

    if latest_version_tag == current_version and DB_PATH.exists():
        logger.info("Database is already up to date.")
        return

    # Find the database asset
    asset_url = None
    for asset in release_info.get("assets", []):
        if asset.get("name") == DB_ASSET_NAME:
            asset_url = asset.get("url")  # Use the API URL for assets
            break

    if not asset_url:
        logger.error(f"Could not find asset '{DB_ASSET_NAME}' in release '{latest_version_tag}'.")
        return

    # Perform the download and update
    if download_db_asset(asset_url):
        update_current_version(latest_version_tag)
    else:
        logger.error(
            "Database update failed. The application will use the existing database if available.")


async def periodic_db_updater():
    """Runs the database check periodically in an infinite loop."""
    logger.info("Starting periodic database updater...")
    while True:
        await check_and_update_db()
        logger.info(f"Next database check in {CHECK_INTERVAL_SECONDS / 3600:.1f} hours.")
        await asyncio.sleep(CHECK_INTERVAL_SECONDS)
