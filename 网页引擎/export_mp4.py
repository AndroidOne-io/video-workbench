"""明确要求导出时使用；与预览共享 renderAt(t)，不在修改工程时自动运行。"""
import argparse
import base64
import json
import math
import shutil
import subprocess
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--url',required=True,help='已启动的同源预览地址，保留本地高清映射')
    ap.add_argument('--out',type=Path)
    ap.add_argument('--authorized-export',action='store_true',help='仅在用户明确授权导出后使用')
    ap.add_argument('--check-only',action='store_true',help='检查真实素材和静帧，不编码视频')
    ap.add_argument('--start',type=float,default=0)
    ap.add_argument('--duration',type=float,default=None)
    ap.add_argument('--width',type=int,default=1920)
    ap.add_argument('--fps',type=float,default=30)
    ap.add_argument('--speed',type=float,default=1)
    ap.add_argument('--require-hd',action='store_true',help='要求服务至少存在一个本地高清映射')
    args=ap.parse_args()
    if args.width<=0 or args.width%32:ap.error('宽度须为正数且能被32整除')
    if args.fps<=0 or args.fps>120:ap.error('帧率范围为 (0,120]')
    if not .5<=args.speed<=2:ap.error('导出倍速范围为 0.5–2')
    if not args.check_only and (not args.authorized_export or args.out is None):ap.error('导出需要 --authorized-export 和 --out；只验证请使用 --check-only')
    if not math.isfinite(args.start) or args.start<0:ap.error('起点必须为非负有限数')
    if args.duration is not None and (not math.isfinite(args.duration) or args.duration<=0):ap.error('时长必须为正有限数')
    if args.out and args.out.exists():ap.error('输出文件已存在，请换文件名以保留旧版')
    if args.require_hd:
        u=urllib.parse.urljoin(args.url,'/__local_hd_status__')
        state=json.load(urllib.request.urlopen(u,timeout=10))
        if not state.get('originals'):ap.error('未检测到本地高清映射')
    if not args.check_only and not shutil.which('ffmpeg'):ap.error('请先安装 ffmpeg')
    from playwright.sync_api import sync_playwright
    if not args.check_only:args.out.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='video-workbench-') as folder:
        video=Path(folder)/'video.mp4'; audio=Path(folder)/'audio.bin'
        with sync_playwright() as p:
            browser=p.chromium.launch(channel='chrome',args=['--autoplay-policy=no-user-gesture-required'])
            page=browser.new_page(viewport={'width':1920,'height':1200})
            page.goto(args.url);page.wait_for_function('window.READY===true',timeout=180000)
            bad=page.evaluate('E.probeVideos(60000)')
            if bad:raise RuntimeError(f'素材不可读，停止导出，不回退低清代理：{bad}')
            total=page.evaluate('window.VIDEO_PROJECT.duration')
            if args.start>=total:raise ValueError('起点超出时间线')
            source_duration=min(total-args.start,args.duration if args.duration is not None else total)
            duration=source_duration/args.speed
            if args.check_only:
                for t in [args.start,args.start+source_duration/2,max(args.start,args.start+source_duration-1/args.fps)]:
                    page.evaluate('async t=>{await window.renderAt(t);return document.getElementById("c").toDataURL()}',t)
                page.wait_for_function('document.getElementById("mix").readyState>=2')
                print('CHECK_OK: media decoded, audio loaded, browser renderAt produced three still frames; no video exported')
                browser.close()
                return
            audio_url=page.evaluate("document.getElementById('mix').src")
            # 与画面读取同一个预览服务的音轨。
            urllib.request.urlretrieve(audio_url,audio)
            hw='h264_videotoolbox' in subprocess.run(['ffmpeg','-hide_banner','-encoders'],capture_output=True,text=True).stdout
            enc=['-c:v','h264_videotoolbox','-b:v','24M'] if hw else ['-c:v','libx264','-preset','veryfast','-crf','18']
            cmd=['ffmpeg','-v','error','-y','-f','image2pipe','-framerate',str(args.fps),'-c:v','mjpeg','-i','-',
                 '-vf',f'scale={args.width}:{args.width*9//16}:flags=lanczos',*enc,'-pix_fmt','yuv420p',str(video)]
            ff=subprocess.Popen(cmd,stdin=subprocess.PIPE)
            try:
                frames=math.ceil(duration*args.fps)
                for n in range(frames):
                    t=args.start+n/args.fps*args.speed
                    frame=page.evaluate("""async t => {
                        await window.renderAt(t);
                        return document.getElementById('c').toDataURL('image/jpeg',.95);
                    }""",t)
                    ff.stdin.write(base64.b64decode(frame.split(',',1)[1]))
                    if n%60==0:print(f'{n}/{frames} 帧',flush=True)
                ff.stdin.close()
                if ff.wait()!=0:raise RuntimeError('视频编码失败')
            finally:
                if ff.poll() is None:ff.terminate();ff.wait()
                browser.close()
        # 声音用 atempo 保持音高；预览输入框的倍速不决定导出速度。
        subprocess.run(['ffmpeg','-v','error','-n','-i',str(video),'-ss',str(args.start),'-i',str(audio),
                        '-map','0:v:0','-map','1:a:0','-c:v','copy','-af',f'atempo={args.speed}',
                        '-c:a','aac','-b:a','256k','-t',str(duration),'-shortest','-movflags','+faststart',str(args.out)],check=True)
    print(f'完成：{args.out}；预计 {duration:.3f}s',flush=True)


if __name__=='__main__':main()
