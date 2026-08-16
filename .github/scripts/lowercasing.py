from contextlib import chdir
from pathlib import Path

import git
cwdString = "../../"
cwd = Path(cwdString)
directory = Path("00 Data Files")

allowed_suffixes = [
    # ".nif",
    # ".kf",
    ".dds",
    # ".tga",
    # ".mp3",
    # ".wav"
]
suffix = "*.dds"

current_repo = git.Repo(cwdString)
with chdir(cwd):
    for file_path in directory.rglob(suffix):
        print(file_path)
        if file_path.name.__contains__("Deshaan"):
            test = file_path.parts
            print(file_path)