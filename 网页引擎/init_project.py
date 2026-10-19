"""从参考引擎创建独立项目，不覆盖已有文件；只生成预览工程。"""
import argparse
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('destination', type=Path)
    args = ap.parse_args()
    dest = args.destination.resolve()
    if dest.exists():
        ap.error('目标目录已存在，请选择新目录以免覆盖工程')
    shutil.copytree(HERE / '模板', dest)
    for filename in ['engine.js', 'player.js', 'serve.py', 'export_mp4.py']:
        shutil.copy2(HERE / filename, dest / filename)
    subprocess.run([sys.executable, str(dest/'build.py')],check=True)
    print(f'启动：python3 "{dest / "serve.py"}" --port 8771')


if __name__ == '__main__':
    main()
