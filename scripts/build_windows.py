"""Build a self-contained Windows x64 folder/ZIP from source, excluding all user data."""
import hashlib
import importlib.metadata
from pathlib import Path
import shutil
import subprocess
import sys
import tomllib
import zipfile


def main():
    if sys.platform != 'win32':
        raise SystemExit('O pacote Windows deve ser compilado no Windows.')
    root = Path(__file__).resolve().parent.parent
    dist, build = (root / 'dist').resolve(), (root / 'build').resolve()
    if not dist.is_relative_to(root) or not build.is_relative_to(root):
        raise SystemExit('As pastas de compilação precisam ficar dentro do projeto.')
    version = tomllib.loads((root / 'pyproject.toml').read_text(encoding='utf-8'))['project']['version']
    subprocess.run([sys.executable, '-m', 'PyInstaller', '--clean', '--noconfirm', '--windowed', '--onedir',
                    '--name', 'KiKi', '--collect-data', 'kiki', '--distpath', str(dist),
                    '--workpath', str(build / 'pyinstaller'), '--specpath', str(build),
                    str(root / 'kiki' / '__main__.py')], cwd=root, check=True)
    bundle = dist / 'KiKi'
    shutil.copy2(root / 'docs' / 'USO-WINDOWS.md', bundle / 'LEIA-ME.txt')
    shutil.copy2(root / 'THIRD_PARTY_NOTICES.md', bundle / 'THIRD_PARTY_NOTICES.md')
    licenses = bundle / 'LICENSES'
    licenses.mkdir(exist_ok=True)
    python_root = Path(sys.base_prefix)
    shutil.copy2(python_root / 'LICENSE.txt', licenses / 'Python.txt')
    if (python_root / 'licenses').is_dir():
        shutil.copytree(python_root / 'licenses', licenses / 'Python-dependencies', dirs_exist_ok=True)
    for index, license_file in enumerate((python_root / 'tcl').rglob('license.terms')):
        shutil.copy2(license_file, licenses / f'Tcl-Tk-{index}.txt')
    distribution = importlib.metadata.distribution('pyinstaller')
    for file in distribution.files or ():
        if file.name == 'COPYING.txt':
            shutil.copy2(distribution.locate_file(file), licenses / 'PyInstaller.txt')
    files = sorted(path for path in bundle.rglob('*') if path.is_file())
    forbidden = [path for path in files if '.sqlite3' in path.name.lower() or path.suffix.lower() in ('.db', '.log') or path.name == '.env']
    if forbidden:
        raise SystemExit('Compilação contém arquivos de dados proibidos: ' + ', '.join(str(path) for path in forbidden))
    archive = dist / f'KiKi-{version}-windows-x64.zip'
    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED) as output:
        for path in files:
            output.write(path, path.relative_to(dist))
    checksum = hashlib.sha256(archive.read_bytes()).hexdigest()
    (dist / 'SHA256SUMS.txt').write_text(f'{checksum}  {archive.name}\n', encoding='utf-8')
    print(f'Pacote: {archive}\nSHA-256: {checksum}')


if __name__ == '__main__':
    main()
