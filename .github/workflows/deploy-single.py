import os
import git
import github
import subprocess
import shutil 
import logging
import sys

from datetime import datetime
from github.GitRelease import GitRelease


compression_timeout = int(os.environ.get("COMPRESSION_TIMEOUT", 120))
logfile_name: str = os.environ.get("LOGFILE_NAME", "full_output.log")
logfile_7z_name: str = os.environ.get("ARCHIVE_SUBPROCESS_LOG", "f7z_output.log ")
since_release: bool = os.environ.get("SINCE_RELEASE", "False") == "True"
adjusted_date_since: datetime = datetime.fromisoformat(os.environ.get("ADJUSTED_DATE_SINCE", "2025-05-01"))
github_repository = os.environ.get("GITHUB_REPOSITORY", "TD-Addon/TamrielDataMain")
dry_run: bool = os.environ.get("DRY_RUN", "TRUE") == "TRUE"

logger = logging.getLogger("tamriel_data_patch_archiver")

def configure_logging() -> None:    
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(levelname)s: %(name)s: %(message)s')
    # File Logging
    file_logging = logging.FileHandler(logfile_name)
    file_logging.setLevel(logging.DEBUG)    
    file_logging.setFormatter(formatter)
    logger.addHandler(file_logging)
    # Console output
    console_log = logging.StreamHandler(sys.stdout)
    console_log.setLevel(logging.INFO)
    console_log.setFormatter(formatter)
    logger.addHandler(console_log)


def get_changed_files(since_date: str) -> list[str]:
    current_repo = git.Repo("")
    logger.info(f"Current ref is: {current_repo.head.ref}")
    commitsline = list(current_repo.iter_commits("main", since=since_date))
    changed_files = set()
    commitsline.reverse()
    for specific_commit in commitsline:
        logger.debug(f"Processing commit: {specific_commit.hexsha}")
        diffs = specific_commit.parents[0].diff(specific_commit)
        for filediff in diffs:
            filename = filediff.b_path
            if not filename.startswith("00 Data Files/"):
                continue
            logger.debug(f"Found {filediff.change_type} file:{filename}")
            if filediff.deleted_file:
                changed_files.discard(filename)
                continue
            if filediff.renamed_file:
                 changed_files.discard(filediff.rename_from)
            changed_files.add(filename)
    return changed_files

def create_archive(release_dir: str) -> str:
    logger.info("Compressing...")
    timestamp = datetime.now().strftime("%Y-%m-%d")
    data_dir = f"{release_dir}/00 Data Files/"
    zip_path = os.path.abspath(f"Tamriel-Data-Addon-{timestamp}.7z")
    try:
        with open(logfile_7z_name, "w") as log_file:
            subprocess.run(["7z", "a", zip_path, "./*", "-y"], cwd=data_dir, check=True, stdout=log_file, stderr=log_file, timeout=compression_timeout)
    except subprocess.TimeoutExpired:
        logger.error("Killed archiving process as it took to long")
        exit(0)
    logger.info(f"Archive Created: {zip_path}")
    return zip_path

def move_files(changed_files) -> None:
    logger.info("Moving files")
    for file in changed_files:        
        file_src = os.path.abspath(f"./{file}")
        file_dst = os.path.abspath(f"./{release_dir}/{file}")
        os.makedirs(os.path.dirname(f"{release_dir}/{file}"), exist_ok=True)
        shutil.copyfile(src=file_src, dst=file_dst)

        # Update modified time for the ESM
        if file.endswith("Tamriel_Data.esm"):
            logger.info("Updating modified time for Tamriel_Data.esm")
            os.utime(file_dst, (os.stat(file_dst).st_atime, 1325376000))  

def fetch_release() -> GitRelease:
    if(dry_run):
        logger.info("Skipping retrieving release info")
        return None
    logger.info("Authenticating...")
    token = github.Auth.Token(os.environ["GITHUB_TOKEN"])
    gh = github.Github(auth=token)
    repo = gh.get_repo(github_repository)

    # # Get the latest release
    logger.info("Retrieving latest release...")
    release = repo.get_latest_release()
    release_tag = repo.get_git_ref(f"tags/{release.tag_name}")
    release_sha = release_tag.object.sha
    logger.info(f"Latest release SHA: {release_sha}")
    return release

def update_release(release: GitRelease) -> None:
    if(dry_run):
        logger.info("Skipping updating release to github")
        return
    logger.info("Updating Release")
    for asset in release.get_assets():
        if "Tamriel-Data-Addon" in asset.name:
            logger.info(f"Deleting old nightly asset from release: {asset.name}")
            asset.delete_asset()
    logger.info("Uploading...")
    release.upload_asset(
        path=zip_path,
        name=os.path.basename(zip_path),
        content_type="application/x-7z-compressed",
    )

if __name__ == "__main__":
    configure_logging()
    # Fetch latest release information
    release = fetch_release()

    # Swap to different date from yaml if False
    since_date = release.created_at if since_release else adjusted_date_since

    # Find the changed files
    logger.info(f"Retrieving changed files since {since_date}...")
    changed_files = get_changed_files(since_date)
    release_dir = "new_release"
    if num_changes := len(changed_files):
        logger.info(f"Found {num_changes} changed files.")
        os.makedirs(release_dir, exist_ok=True)
    else:
        logger.warning("No changes found.")
        exit(0)
    
    # Move files into seperate directory for the archive
    move_files(changed_files)   

    # Compress the "00 Data Files" directory
    zip_path = create_archive(release_dir)

    # Upload new archive in release
    update_release(release)
    logger.info("Finished")
