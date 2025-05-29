import os
import base64
import github
import subprocess

from datetime import datetime
from github.Repository import Repository


def get_changed_files(repo: Repository, since: datetime) -> set[str]:
    """Get the set of changed files in the repository since a given date."""

    # Doing this manually instead of using `repo.compare()` as that method
    # had both timeout issues and did not return the full list of changes.
    commits = repo.get_commits(since=since, until=datetime.now())

    changed_files = set()

    for commit in commits.reversed:
        print(f"Processing commit: {commit.sha}")
        for file in commit.files:
            if not file.filename.startswith("00 Data Files/"):
                continue

            print(f"Found {file.status} file: {file.filename}")

            if file.status == "removed":
                changed_files.discard(file.filename)
                continue

            if file.status == "renamed":
                changed_files.discard(file.previous_filename)

            changed_files.add(file.filename)

    return changed_files


if __name__ == "__main__":
    print("Authenticating...")
    token = github.Auth.Token(os.environ["GITHUB_TOKEN"])
    gh = github.Github(auth=token)
    repo = gh.get_repo(os.environ["GITHUB_REPOSITORY"])

    # Get the latest release
    print("Retrieving latest release...")
    release = repo.get_latest_release()
    release_tag = repo.get_git_ref(f"tags/{release.tag_name}")
    release_sha = release_tag.object.sha
    print(f"Latest release SHA: {release_sha}")

    # Get the current branch
    print("Retrieving current branch...")
    current_branch = repo.get_branch(repo.default_branch)
    current_sha = current_branch.commit.sha
    print(f"Current branch SHA: {current_sha}")

    # Find the changed files
    print("Retrieving changed files...")
    changed_files = get_changed_files(repo, since=release.created_at)

    if num_changes := len(changed_files):
        print(f"Found {num_changes} changed files.")
    else:
        print("No changes found.")
        exit(0)

    for file in changed_files:
        os.makedirs(os.path.dirname(file), exist_ok=True)

        print("Downloading:", file)
        file_content = repo.get_contents(file, ref=current_sha)

        with open(file, "wb") as f:
            if file_content.encoding == "base64":
                content = file_content.decoded_content
            else:
                # For binary files go through git blob instead.
                blob = repo.get_git_blob(file_content.sha)
                content = base64.b64decode(blob.content)

            print("Writing:", file)
            f.write(content)

        # Update modified time for the ESM
        if file.endswith("Tamriel_Data.esm"):
            print("Updating modified time for Tamriel_Data.esm")
            os.utime(file, (os.stat(file).st_atime, 1325433600))

    # Compress the "00 Data Files" directory
    print("Compressing...")
    timestamp = datetime.now().strftime("%Y-%m-%d")
    data_dir = "00 Data Files"
    zip_path = os.path.abspath(f"Tamriel-Data-Addon-{timestamp}.7z")
    subprocess.run(["7z", "a", zip_path, "./*"], cwd=data_dir, check=True)

    print(f"Archive Created: {zip_path}")

    # Delete old archives
    for asset in release.get_assets():
        if "Tamriel-Data-Addon" in asset.name:
            print(f"Deleting old nightly asset from release: {asset.name}")
            asset.delete_asset()

    # Upload new archive
    print("Uploading...")
    release.upload_asset(
        path=zip_path,
        name=os.path.basename(zip_path),
        content_type="application/x-7z-compressed",
    )

    print("Finished")
