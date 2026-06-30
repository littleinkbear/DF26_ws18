# -*- coding: utf-8 -*-
"""
frame_to_video.py —— 把一个图片序列文件夹合成 GIF 或 MP4

用法：
    1. 改下面【全局参数】区的变量（输入文件夹、输出格式、帧率等）
    2. 终端运行：  python frame_to_video.py

依赖说明：
    - GIF 输出：只需要 Pillow（PIL），本机已装，开箱即用。
    - MP4 输出：需要 imageio[ffmpeg] 或系统 ffmpeg。本机当前都没装，
      所以若把 OUTPUT_FORMAT 设成 "mp4" 而环境缺依赖，脚本会自动
      退回生成 GIF，并打印提示，不会报错中断。
"""

import sys
from pathlib import Path

# Windows 终端默认 cp950/gbk 编码，打印简体中文会报 UnicodeEncodeError，
# 这里强制把标准输出改成 UTF-8，保证中文提示正常显示。
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# ============================================================
# 【全局参数】—— 改这里就行，全部集中在文件顶部
# ============================================================

# 输入：存放图片帧的文件夹
INPUT_DIR = r"C:\Users\GAI\Downloads\frames"

# 输出文件路径（后缀会按 OUTPUT_FORMAT 自动改，可不用纠结后缀）
OUTPUT_PATH = r"C:\Users\GAI\Downloads\frames_out"

# 输出格式："gif" 或 "mp4"
OUTPUT_FORMAT = "gif"

# 帧率：每秒多少张图（数字越大播放越快）
FPS = 12

# 匹配哪些图片（按文件名排序，确保帧顺序正确）
# 默认 png；要其它格式改成 "*.jpg" 等
PATTERN = "*.png"

# 缩放：把每帧宽度缩到这个像素（高度等比）。设 None 表示不缩放。
# GIF 体积大，建议缩到 800~1000；MP4 可设 None 保持原尺寸。
RESIZE_WIDTH = None

# GIF 是否循环播放：0 = 无限循环；其它数字 = 循环几次
GIF_LOOP = 0

# ============================================================
# 以下为实现，一般不用改
# ============================================================


def collect_frames(input_dir, pattern):
    """收集并按文件名排序所有帧的路径，返回 list[Path]。"""
    files = sorted(Path(input_dir).glob(pattern))  # glob + 排序保证 00,01,02… 顺序
    if not files:
        sys.exit(f"[错误] 在 {input_dir} 找不到匹配 {pattern} 的图片")
    print(f"[信息] 找到 {len(files)} 帧")
    return files


def load_resized(path, width):
    """读取一张图；若指定宽度则等比缩放。返回 PIL.Image。"""
    from PIL import Image

    img = Image.open(path).convert("RGB")  # 统一转 RGB，避免调色板/透明通道问题
    if width:  # 需要缩放时按宽度等比算高度
        h = int(img.height * width / img.width)
        img = img.resize((width, h), Image.LANCZOS)  # LANCZOS：高质量缩放
    return img


def make_gif(files, out_path, fps, width, loop):
    """用 Pillow 合成 GIF。"""
    out_path = Path(out_path).with_suffix(".gif")
    duration = int(1000 / fps)  # GIF 每帧停留毫秒数 = 1000/帧率
    frames = [load_resized(f, width) for f in files]  # 全部读进内存（帧多时占内存）
    frames[0].save(  # 第一帧带头，append_images 接后续帧
        out_path,
        save_all=True,
        append_images=frames[1:],
        duration=duration,
        loop=loop,
        optimize=True,  # 压缩调色板，减小体积
    )
    print(f"[完成] GIF 已生成 → {out_path}")


def make_mp4(files, out_path, fps, width):
    """
    用 imageio 合成 MP4。
    若 imageio / ffmpeg 缺失，抛 ImportError，由调用方退回 GIF。
    """
    import numpy as np  # imageio 写帧需要 ndarray
    import imageio.v2 as imageio  # 缺这两个就会 ImportError → 触发退回

    out_path = Path(out_path).with_suffix(".mp4")
    writer = imageio.get_writer(out_path, fps=fps, codec="libx264")
    for f in files:
        img = load_resized(f, width)
        writer.append_data(np.asarray(img))  # PIL.Image → ndarray 写入
    writer.close()
    print(f"[完成] MP4 已生成 → {out_path}")


def main():
    files = collect_frames(INPUT_DIR, PATTERN)

    fmt = OUTPUT_FORMAT.lower()
    if fmt == "mp4":
        try:
            make_mp4(files, OUTPUT_PATH, FPS, RESIZE_WIDTH)
        except ImportError:
            # 缺 imageio/ffmpeg：不报错中断，自动退回 GIF
            print("[警告] 缺少 imageio 或 ffmpeg，无法输出 MP4，自动改输出 GIF。")
            print("       想要 MP4 请先装： pip install imageio[ffmpeg]")
            make_gif(files, OUTPUT_PATH, FPS, RESIZE_WIDTH, GIF_LOOP)
    else:
        make_gif(files, OUTPUT_PATH, FPS, RESIZE_WIDTH, GIF_LOOP)


if __name__ == "__main__":
    main()
