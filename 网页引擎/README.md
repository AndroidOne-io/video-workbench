# 浏览器剪辑预览工程

从 STEPX 剪辑工程提取的轻量参考实现：纯 HTML + JavaScript + Canvas，预览不需要 npm、不需要先编码整条视频。来源基线：[StepXNeoDY / edit-final-20261017](https://github.com/AndroidOne-io/StepXNeoDY/tree/edit-final-20261017/剪辑工程)。

先读 [实现与复用指南](实现与复用指南.md)。这是带可运行样例的起步模板，不是自动完成转写、剪辑和配乐的一键成片工具。

## 新一期怎么开始

```bash
# destination 必须是不存在的新目录，不覆盖现有项目
python3 网页引擎/init_project.py /你的新项目/剪辑预览
python3 /你的新项目/剪辑预览/serve.py --port 8771
```

打开 http://127.0.0.1:8771/index.html 。初始工程是 6 秒静音动画示例，生成的 WAV 只用于演示播放器时钟，不是配音。

每期主要修改以下文件：

| 文件 | 改什么 |
| --- | --- |
| `project.json` | 镜头时间、字幕、事件、音轨路径、视频和图片清单 |
| `scenes.js` | 每个镜头怎么画、素材取哪一段、动画与关键词怎样对齐 |
| `assets/` | 预先制作好的图片、复杂文字、背景等 |
| `mix.m4a` 等音轨 | 把本期口播、配乐、音效混成一条；在 project.json.audio 指定 |
| `index.html` 字体声明 | 正式交付应随项目提供有使用权的字体，不能依赖本机字体 |

改完数据运行 `python3 build.py` 再刷新；只改 `scenes.js` 直接刷新。源录音不用被覆盖。模板 `build.py` 负责数据校验和写 JS，不做 ASR、音频剪接或混音；成熟项目可用自己的构建器输出同样的数据接口。

## 本地高清与在线素材共用 URL

项目里保留便携素材路径，例如 `media/08.mp4`。本地创建 `.local/media.json`：

```json
{
  "media/08.mp4": ".local/originals/08.mp4"
}
```

把高清原片实际复制到 `.local/originals/08.mp4`，或在本地映射中填写自己的绝对路径。`.local/` 被 Git 忽略，路径不写进共享 JS。重启服务后，同一个 `media/08.mp4` URL 本地读取高清文件；其他人没有映射时仍读取项目便携素材。映射写了但原片不存在会明确报错，不静默退回低清。

访问 `/__local_hd_status__` 查看启用的映射，素材响应头 `X-Local-Media: original` 表示读取原片。状态里存在映射不代表每一份素材都是高清，需要对照实际 sources 清单逐项核验。避免把原片只做成指向另一个可删除仓库的软链接。

## 明确要求导出时

预览、截图和修改字幕不触发视频导出。用户要求成片后，再使用运行着的同一个服务：

```bash
# 需要本机 Chrome、FFmpeg；uv 只为导出脚本提供 Playwright
uv run --with playwright python export_mp4.py \
  --url http://127.0.0.1:8771/index.html \
  --out output/成片_2K_1.1倍速.mp4 \
  --width 2560 --fps 30 --speed 1.1 --require-hd
```

- `--speed` 明确决定成片倍速，预览输入框的倍速不会自动带入导出。
- `--require-hd` 检查服务有本地高清映射，不是全素材分辨率认证；逐项检查仍需在导出前完成。
- 素材读不了就报错，不自动回退低清代理。已有输出文件不覆盖。
- 当前引擎逻辑画布为 1920×1080，2560×1440 输出用 Lanczos 放大，**不是原生 2K 画布合成**。高清源可以改善裁切细节，但不能凭此恢复不存在的文字细节。
- 通用导出器先保留单进程，降低视频解码资源争抢。STEPX 的并行导出器可作后续优化参考，先实测内存和解码能力，不默认堆到 6 个浏览器。

## 复用边界

`engine.js` 和 `player.js` 提取自已使用过的工程；播放器去掉 STEPX 专用存储键，音轨改为数据配置。启动器、通用 HTTP 服务、最小数据构建器及单进程导出器为本次新增适配。既有 STEPX 项目没有被迁移到此模板。

先用模板完成本期素材的播放和跳转检查，再接复杂效果。横竖屏切换、原生 2K 合成、自动 ASR、完整音轨编辑器不在本模板能力范围内。

## 模板验证

```bash
python3 -m unittest discover -s 网页引擎/tests -p 'test_*.py'
# 启动刚生成的6秒示例后，再执行浏览器集成检查
uv run --with playwright python 网页引擎/tests/smoke_browser.py http://127.0.0.1:8771/index.html
```

已验证：单段/后缀/开放尾部 Range、本地原片覆盖、缺失原片报错、示例播放、镜头跳转、1.10倍速和同一时刻重复取帧一致。示例没有真实视频，素材解码性能需要接入本期真实素材后再核验。测试不导出视频。
