import hashlib
import os
import shutil
from pathlib import Path

BLOCKSIZE = 65536


def hash_file(path: Path):
    hasher = hashlib.sha1()
    with path.open("rb") as file:
        buf = file.read(BLOCKSIZE)
        while buf:
            hasher.update(buf)
            buf = file.read(BLOCKSIZE)
    return hasher.hexdigest()


def read_paths_and_hashes(root):
    hashes = {}
    for folder, _, files in os.walk(root):
        for fn in files:
            abspath = Path(folder) / fn
            relpath = abspath.relative_to(root)
            hashes[hash_file(Path(folder) / fn)] = relpath
    return hashes


def determine_actions(
    source_hashes: dict, dest_hashes: dict, source_folder, dest_folder
):
    for sha, relpath in source_hashes.items():
        if sha not in dest_hashes:
            sourcepath = Path(source_folder) / relpath
            destpath = Path(dest_folder) / relpath
            yield "COPY", sourcepath, destpath

        elif dest_hashes[sha] != relpath:
            olddestpath = Path(dest_folder) / dest_hashes[sha]
            newdestpath = Path(dest_folder) / relpath
            yield "MOVE", olddestpath, newdestpath

    for sha, relpath in dest_hashes.items():
        if sha not in source_hashes:
            yield "DELETE", dest_folder / relpath


def sync(source: Path, dest: Path):
    source_hashes = read_paths_and_hashes(source)
    dest_hashes = read_paths_and_hashes(dest)

    actions = determine_actions(source_hashes, dest_hashes, source, dest)

    for action, *paths in actions:
        if action == "COPY":
            shutil.copyfile(*paths)

        elif action == "MOVE":
            paths[1].parent.mkdir(parents=True, exist_ok=True)
            shutil.move(*paths)

        else:
            paths[0].unlink()
