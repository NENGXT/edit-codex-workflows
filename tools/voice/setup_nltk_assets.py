"""Pinned official NLTK resources for GPT-SoVITS's English text frontend.
Standalone setup add-on. No TTS imports, model execution, source or reference edits.
"""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import tempfile
import urllib.request
import zipfile


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def valid(path, item):
    return path.is_file() and not path.is_symlink() and path.stat().st_size == item['size'] and digest(path) == item['sha256']


def write_verified(path, data, item):
    if len(data) != item['size'] or hashlib.sha256(data).hexdigest() != item['sha256']:
        raise RuntimeError('Resource size/hash mismatch: ' + str(path))
    if path.exists():
        if valid(path, item):
            return
        raise RuntimeError('Existing resource differs; inspect before replacing: ' + str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=path.name + '.', suffix='.partial', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as f:
            f.write(data)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def prepare(root, manifest_path, allow_downloads=False):
    target = root.resolve() / 'nltk_data'
    manifest = json.loads(manifest_path.read_text())
    for resource in manifest['resources']:
        archive = target / resource['path']
        if not valid(archive, resource):
            if archive.exists():
                raise RuntimeError('Existing ZIP hash mismatch: ' + str(archive))
            if not allow_downloads:
                raise RuntimeError('Missing ZIP; run authorized setup first: ' + str(archive))
            expected = 'https://raw.githubusercontent.com/nltk/nltk_data/gh-pages/packages/'
            if resource['url'] != expected + resource['path']:
                raise RuntimeError('Not an expected official NLTK resource URL')
            with urllib.request.urlopen(resource['url'], timeout=90) as response:
                data = response.read(resource['size'] + 1)
            write_verified(archive, data, resource)
        # Parse only after verifying the complete archive. Never unpickle legacy tagger.
        with zipfile.ZipFile(archive) as z:
            members = {}
            for member in z.infolist():
                name = PurePosixPath(member.filename)
                if name.is_absolute() or '..' in name.parts or name.parts[0] != resource['id']:
                    raise RuntimeError('Unsafe archive path')
                if ((member.external_attr >> 16) & 0o170000) == 0o120000:
                    raise RuntimeError('Archive symlink rejected')
                if not member.is_dir():
                    key = str(PurePosixPath(resource['path']).parent / name)
                    if key in members:
                        raise RuntimeError('Duplicate archive member')
                    members[key] = member
            if set(members) != {item['path'] for item in resource['files']}:
                raise RuntimeError('Archive members do not match pinned manifest')
            for item in resource['files']:
                dest = target / item['path']
                if not valid(dest, item):
                    if not allow_downloads:
                        raise RuntimeError('Missing or modified extracted file: ' + str(dest))
                    write_verified(dest, z.read(members[item['path']]), item)
        print('NLTK_VERIFIED', resource['id'], flush=True)
    print('Set NLTK_DATA=' + str(target) + ' before starting inference.', flush=True)
    return target


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--manifest', type=Path, default=Path(__file__).with_name('nltk-assets-manifest.json'))
    p.add_argument('--allow-downloads', action='store_true')
    args = p.parse_args()
    prepare(args.root, args.manifest, args.allow_downloads)
