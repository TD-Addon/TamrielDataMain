from contextlib import chdir
from pathlib import Path, PurePath

import git
cwdString = "../../"
cwd = Path(cwdString)
directory = Path("00 Data Files")

allowed_suffixes = [
    ".nif",
    # ".kf",
    # ".dds",
    # ".tga",
    # ".mp3",
    # ".wav"
]

current_repo = git.Repo(cwdString)
file_limit = 2000
current_file_count = 0

with chdir(cwd):
    for file_path in directory.rglob("*"):
        if current_file_count > file_limit:
            break
        else:
            if file_path.suffix in allowed_suffixes:
                if any(c.isupper() for c in file_path.name):
                    new_filename = file_path.name.lower()
                    parent_paths = file_path.parts[:-1]
                    new_path = parent_paths + (new_filename,)
                    new_purepath = PurePath(*new_path)
                    current_repo.index.move([file_path, new_purepath])
                    current_file_count += 1
                    # print(file_path)
