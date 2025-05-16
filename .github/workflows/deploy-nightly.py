import os
import base64
import github
import subprocess

from datetime import datetime


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
    print("Comparing changed files...")
    comparison = repo.compare(release_sha, current_sha)
    changed_files = [f.filename for f in comparison.files if f.status != "removed"]

    # Ignore stuff outside of the "00 Data Files" directory
    changed_files = [f for f in changed_files if f.startswith("00 Data Files/")]

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
            os.utime(file, (os.stat(file).st_atime, 1325458800))

    # Compress the "00 Data Files" directory
    print("Compressing...")
    timestamp = datetime.now().strftime("%Y-%m-%d")
    data_dir = "00 Data Files"
    zip_path = os.path.abspath(f"Tamriel-Data-Nightly-{timestamp}.7z")
    subprocess.run(["7z", "a", zip_path, "./*"], cwd=data_dir, check=True)

    print(f"Archive Created: {zip_path}")

    # Delete old archives
    for asset in release.get_assets():
        if "Tamriel-Data-Nightly" in asset.name:
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
