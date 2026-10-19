"""对刚创建的静音示例做浏览器集成检查；只取静帧，不导出视频。
uv run --with playwright python tests/smoke_browser.py http://127.0.0.1:8771/index.html
"""
import sys
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser=p.chromium.launch(channel='chrome',args=['--autoplay-policy=no-user-gesture-required'])
    page=browser.new_page()
    errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto(sys.argv[1]);page.wait_for_function('window.READY===true')
    assert page.evaluate('D.DUR')==6
    assert page.evaluate('E.probeVideos()')==[]
    def frame(t):
        return page.evaluate('''async t => {
          await window.renderAt(t);
          return document.getElementById('c').toDataURL();
        }''',t)
    a=frame(1.5);b=frame(4.5);again=frame(1.5)
    assert a!=b and a==again,'拖动前后同一时间点必须得到相同画面'
    page.locator('#speed').fill('1.10');page.locator('#speed').press('Enter')
    assert abs(page.evaluate("document.getElementById('mix').playbackRate")-1.1)<1e-6
    page.locator('#jump').select_option('2')
    page.wait_for_function('window.player.t===3')
    page.locator('#play').click();page.wait_for_function('window.player.t>3.2')
    page.locator('#play').click()
    assert errors==[],errors
    print('PASS: 两镜画面、确定性回看、镜头跳转、1.10倍速、音频时钟播放；未导出视频')
    browser.close()
