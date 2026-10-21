"""Install an explicitly selected runtime version; never overwrite local edits silently."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

HERE=Path(__file__).resolve().parent
FILES=('engine.js','player-ui.js','player.js','style.css','export_mp4.py')
LOCK='player-lock.json'
def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
def install(destination,adopt=False,check=False):
    dest=Path(destination).resolve()
    if not dest.is_dir():
        raise ValueError('目标必须是已有项目目录')
    old=json.loads((dest/LOCK).read_text()) if (dest/LOCK).exists() else {}
    for name in FILES:
        target=dest/name
        if target.is_symlink():
            raise ValueError(f'拒绝修改软链接：{name}')
        if target.exists() and digest(target)!=old.get('sha256',{}).get(name) and not adopt:
            raise ValueError(f'文件未经版本记录或已有本地修改：{name}；人工核对后可用 --adopt 接入')
    if check:
        if old.get('version')!=(HERE/'VERSION').read_text().strip() or any(not (dest/n).exists() or digest(dest/n)!=digest(HERE/n) for n in FILES):
            raise ValueError('项目与当前公共版本不一致')
        return old
    hashes={n:digest(HERE/n) for n in FILES}
    for name in FILES:
        shutil.copy2(HERE/name,dest/name)
    lock={'schema':1,'api':1,'source':'https://github.com/AndroidOne-io/video-workbench','version':(HERE/'VERSION').read_text().strip(),'sha256':hashes}
    (dest/LOCK).write_text(json.dumps(lock,indent=2)+'\n')
    return lock

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('destination',type=Path)
    p.add_argument('--adopt',action='store_true',help='首次接入旧项目：人工核对后替换公共文件')
    p.add_argument('--check',action='store_true',help='只核对版本与文件内容')
    a=p.parse_args()
    try: result=install(a.destination,a.adopt,a.check)
    except (ValueError,OSError) as exc:p.exit(1,str(exc)+'\n')
    print(('Verified' if a.check else 'Installed')+' player '+result['version'])
if __name__=='__main__':main()
