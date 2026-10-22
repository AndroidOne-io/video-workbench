# 公共网页播放器 · 1.0.0

开工先读根目录 [剪辑规矩](../剪辑规矩.md)，本文件负责播放器接口与操作说明；通用制作、交付和经验维护规则以统一入口为准。

以后每期视频沿用这套播放器，只维护本期素材、时间线和场景。纯 HTML + JavaScript + Canvas；浏览器预览无需 npm，也不需要先编码整条视频。播放器来自已使用的阶跃与鹈鹕项目，界面包含逐字稿搜索、字幕开关、静音、全屏、逐帧和 0.25–4.00 倍速。

## 新建一期

```sh
python3 网页引擎/init_project.py /你的新项目/剪辑预览
python3 /你的新项目/剪辑预览/serve.py --port 8771
```

目标目录必须不存在。初始工程是六秒静音示例，WAV 只提供播放器时钟，不是配音。生成后的项目可以独立运行，不依赖公共仓库的位置或网络。

| 本期文件 | 职责 |
| --- | --- |
| `project.json` | 项目 ID、标题、帧率、音轨、镜头、字幕、素材、字体加载项、`sceneScripts` 有序列表 |
| `scenes.js` 或场景列表中的文件 | 每个镜头如何绘制；任意命名，不固定为 s1–s6 |
| `common.js` | 本期时间映射、场景组合与字幕绘制 |
| `preview.js` | 把本期数据适配到公共播放器接口 |
| `assets/`、媒体和混音 | 本期资源，用相对 URL 引用 |
| `fonts.css`、字体文件 | 本期字体声明；正式交付随项目提供有权使用的字体 |

数据改完运行 `python3 build.py`，再刷新网页；只改场景 JS 可直接刷新。`build.py` 生成数据和脚本清单，不做转写、音轨剪接或混音。项目 ID 首次生成后保留，避免不同视频相互覆盖倍速设置。

## 公共与项目的边界

公共文件为 `engine.js`、`player-ui.js`、`player.js`、`style.css`、`export_mp4.py`。这些文件只在本仓库修改，通过安装工具同步；每期不另写播放器。

公共播放器只认识 `E` 引擎与 `window.VIDEO_PROJECT`，不依赖 `D`、`SC`、鹈鹕的插入表或场景名称。`common.js` 里的人物裁切、配色、舞台等属于本期；数学、视频同步、图层、透视等通用方法留在引擎里。

已有项目在场景加载完后提供：

```js
window.VIDEO_PROJECT = {
  id: 'my-video', title: '本期标题',
  duration: 60, fps: 30, audio: 'mix.m4a',
  shots: [{start: 0, end: 60, name: '开场'}],
  captions: [[0, 2, '第一句字幕']], // [开始秒, 结束秒, 文本]
  images: ['background.png'], // 相对于 assets/，可为空
  fonts: ['58px Sub'], // 与项目 fonts.css 一致，可为空
  draw: frame // frame(ctx, 成片时间秒, 是否显示字幕)
};
```

可选 `mark`、`subtitle`、`note` 仅影响播放器界面。`draw` 必须根据时间确定画面，不依赖累计帧数；字幕开关由第三个参数传入。画面逻辑坐标固定为 1920×1080。使用视频时由项目调用 `E.setVideoSources()`；图片键为去掉 png/jpg 后缀的文件名。

入口顺序为：项目数据 → `engine.js` → 本期素材表与场景 → `preview.js` → `player-ui.js` → `player.js`。入口加载 `style.css` 与项目的 `fonts.css`，body 的控件由公共 UI 生成。可参考模板 `build.py` 生成的入口。

## 固定版本与更新

`player-lock.json` 记录运行版本、API 版本及每个公共文件的 SHA-256。项目保存安装后的文件快照，升级公共工程不会自动改变旧项目。

```sh
# 检查项目是否与当前检出的公共版本一致
python3 网页引擎/sync_runtime.py /项目/剪辑预览 --check
# 显式升级；已有文件若被项目修改，会先报错，完全不写入
python3 网页引擎/sync_runtime.py /项目/剪辑预览
# 首次迁移旧项目：先人工核对文件，再采用公共文件替换
python3 网页引擎/sync_runtime.py /项目/剪辑预览 --adopt
```

升级先在公共仓库检出目标版本，再运行工具。工具只更新公共文件及锁文件，不覆盖项目场景、数据、素材、字体、index 或服务配置。首次接入同时调整入口和 `preview.js`；不要只复制 player.js。旧版模板需按上述 API 迁移，不能直接换播放器脚本。

## 本地高清素材

新项目使用 `.local/media.json`：

```json
{"media/host.mp4": ".local/originals/host.mp4"}
```

服务对相同公共 URL 读取本机原片；其他电脑没有映射时使用仓库便携素材。映射文件及原片不提交。配置了不存在的原片会报错；修改映射后重启服务。访问 `/__local_hd_status__` 查看映射，响应头 `X-Local-Media: original` 表示读取原片。

既有项目可保留自己的 HTTP 服务与高清约定。鹈鹕接入继续使用 `.preview-local.json`，不移动用户原片。服务属于项目基础设施，播放器不读取本机绝对路径。

## 预览与导出使用同一浏览器

导出直接打开同一个网页、调用 `window.renderAt(t)`，等待视频定位后取 Canvas；不再用 Node 原生 Canvas 重画另一遍。实际编码由 FFmpeg 完成，音轨从同一个预览服务读取。

先验证，不生成视频：

```sh
uv run --with playwright python export_mp4.py \
  --url http://127.0.0.1:8771/index.html --check-only
```

只有用户明确要求导出后才使用：

```sh
uv run --with playwright python export_mp4.py \
  --url http://127.0.0.1:8771/index.html \
  --authorized-export --out output/成片.mp4 --width 2560 --fps 30 --speed 1.1
```

需要 Chrome；编码还需要 FFmpeg。`--start`、`--duration` 使用原时间线秒数，`--speed` 明确决定成片倍速，播放器记住的倍速不影响导出。已有输出拒绝覆盖；素材读取或定位失败会中止。`--require-hd` 适用于提供高清状态接口的服务，只检查至少一份映射，不代表全部素材已核验为高清。

输出 2560×1440 使用 1920×1080 画布放大，不宣称原生 2K 合成。只修改、预览、运行测试不会授权导出。

## 渲染提速经验

优化导出前先读 [浏览器视频渲染优化经验](../浏览器视频渲染优化经验.md)：原生 Chrome 架构、WebCodecs 直接编码、离线取帧等待、并行调优，以及画质、帧数、时间戳和音轨验收。文中 198 秒降至 28.53 秒来自另一项目，尚未在当前公共导出器复现；文档列出了现有代码与候选优化的对应位置。

## 测试

```sh
python3 -m unittest discover -s 网页引擎/tests -p 'test_*.py'
node 网页引擎/tests/test_player.cjs
# 先创建并启动六秒样例
uv run --with playwright python 网页引擎/tests/smoke_browser.py http://127.0.0.1:8771/index.html
```

覆盖 HTTP Range、本地高清映射、版本锁与本地修改保护、独立项目 ID、场景列表、导出授权门槛、控件交互、静帧失败传播，以及真实 Chrome 的播放与回看。示例没有视频源，真实素材还需按具体项目检查。没有执行 MP4 编码测试，避免把测试当成视频导出授权。

背景原理及历史接口见 [实现与复用指南](实现与复用指南.md)，当前公共 API 以上述说明为准。
