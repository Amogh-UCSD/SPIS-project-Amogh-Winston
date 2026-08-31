from ipycanvas import Canvas, hold_canvas
import ipywidgets as widgets
from IPython.display import display
import numpy as np
from PIL import Image
import imageio
import io

try:
    from google.colab import files as colab_files
    IN_COLAB = True
except Exception:
    IN_COLAB = False

# =========================
# CONFIG
# =========================
WIDTH, HEIGHT = 600, 600
THUMB_SIZE = 64

# =========================
# STATE
# =========================
draw_color = '#171512'
brush_size = 30
fps = 6
drawing = False
last_pos = None
frames = []  # list of numpy RGBA arrays, one per saved frame

# =========================
# CANVAS
# =========================
canvas = Canvas(width=WIDTH, height=HEIGHT, sync_image_data=True)
canvas.fill_style = 'white'
canvas.fill_rect(0, 0, WIDTH, HEIGHT)

def clear_canvas(*_):
    canvas.fill_style = 'white'
    canvas.fill_rect(0, 0, WIDTH, HEIGHT)
    status.value = '画布已清空'

def on_mouse_down(x, y):
    global drawing, last_pos
    drawing = True
    last_pos = (x, y)
    with hold_canvas(canvas):
        canvas.fill_style = draw_color
        canvas.fill_circle(x, y, brush_size / 2)

def on_mouse_move(x, y):
    global last_pos
    if not drawing:
        return
    with hold_canvas(canvas):
        canvas.stroke_style = draw_color
        canvas.line_width = brush_size
        canvas.line_cap = 'round'
        if last_pos:
            canvas.stroke_line(last_pos[0], last_pos[1], x, y)
        canvas.fill_style = draw_color
        canvas.fill_circle(x, y, brush_size / 2)
    last_pos = (x, y)

def on_mouse_up(x, y):
    global drawing, last_pos
    drawing = False
    last_pos = None

canvas.on_mouse_down(on_mouse_down)
canvas.on_mouse_move(on_mouse_move)
canvas.on_mouse_up(on_mouse_up)

# =========================
# COLOR SWATCHES
# =========================
palette = ['#171512', '#ffffff', '#c0392b', '#2b5fa8', '#3f8f4f',
           '#e0c22e', '#d98a2b', '#3aa6a0', '#9b4fb0', '#7a5230']

color_buttons = []

def make_color_handler(c):
    def handler(_):
        global draw_color
        draw_color = c
        for b in color_buttons:
            b.style.button_color = b.tag
            b.layout.border = '1px solid #999'
        btn.layout.border = '3px solid orange'
    return handler

color_row_children = []
for c in palette:
    btn = widgets.Button(description='', layout=widgets.Layout(width='28px', height='28px', border='1px solid #999'))
    btn.style.button_color = c
    btn.tag = c
    btn.on_click(make_color_handler(c))
    color_buttons.append(btn)
    color_row_children.append(btn)
color_row = widgets.HBox(color_row_children)

# =========================
# BRUSH SIZE
# =========================
brush_slider = widgets.IntSlider(value=30, min=1, max=100, description='画笔:')

def on_brush_change(change):
    global brush_size
    brush_size = change['new']
brush_slider.observe(on_brush_change, names='value')

# =========================
# FPS
# =========================
fps_slider = widgets.IntSlider(value=6, min=1, max=24, description='帧率:')

def on_fps_change(change):
    global fps
    fps = change['new']
fps_slider.observe(on_fps_change, names='value')

# =========================
# STATUS + FRAME COUNTER
# =========================
status = widgets.Label(value='就绪')
frame_count_label = widgets.Label(value='帧数: 0')

# =========================
# FILMSTRIP
# =========================
filmstrip_box = widgets.HBox([])

def make_thumbnail(arr):
    img = Image.fromarray(arr.astype('uint8'), 'RGBA')
    img.thumbnail((THUMB_SIZE, THUMB_SIZE))
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return buf.getvalue()

def refresh_filmstrip():
    thumbs = []
    for i, arr in enumerate(frames):
        img_widget = widgets.Image(value=make_thumbnail(arr), format='png',
                                    layout=widgets.Layout(width=f'{THUMB_SIZE}px', height=f'{THUMB_SIZE}px', border='1px solid #999'))
        thumbs.append(img_widget)
    filmstrip_box.children = thumbs
    frame_count_label.value = f'帧数: {len(frames)}'

# =========================
# FRAME OPERATIONS
# =========================
def add_frame(_):
    arr = canvas.get_image_data()
    frames.append(arr.copy())
    clear_canvas()
    refresh_filmstrip()
    status.value = f'已保存为第 {len(frames)} 帧'

def keep_frame(_):
    if not frames:
        status.value = '还没有帧可以取回'
        return
    arr = frames[-1]
    canvas.put_image_data(arr, 0, 0)
    status.value = '已取回上一帧'

def delete_last_frame(_):
    if not frames:
        status.value = '没有可删除的帧'
        return
    frames.pop()
    refresh_filmstrip()
    status.value = '已删除最后一帧'

def clear_frames(_):
    frames.clear()
    refresh_filmstrip()
    status.value = '已清空所有帧'

btn_add = widgets.Button(description='保存当前帧', button_style='success')
btn_keep = widgets.Button(description='取回上一帧')
btn_delete = widgets.Button(description='删除最后一帧')
btn_clear_frames = widgets.Button(description='清空所有帧', button_style='danger')
btn_clear_canvas = widgets.Button(description='清空画布')

btn_add.on_click(add_frame)
btn_keep.on_click(keep_frame)
btn_delete.on_click(delete_last_frame)
btn_clear_frames.on_click(clear_frames)
btn_clear_canvas.on_click(clear_canvas)

frame_ops_row = widgets.HBox([btn_add, btn_keep, btn_delete, btn_clear_frames, btn_clear_canvas])

# =========================
# PLAY PREVIEW (using Play widget)
# =========================
preview_image = widgets.Image(format='png', layout=widgets.Layout(width=f'{WIDTH}px', height=f'{HEIGHT}px', border='2px solid #333'))

def frame_to_png_bytes(arr):
    img = Image.fromarray(arr.astype('uint8'), 'RGBA').convert('RGB')
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return buf.getvalue()

def update_preview(change):
    idx = change['new']
    if frames:
        preview_image.value = frame_to_png_bytes(frames[idx % len(frames)])

play_widget = widgets.Play(value=0, min=0, max=0, interval=1000 // fps, description='播放')
frame_slider = widgets.IntSlider(value=0, min=0, max=0)
widgets.jslink((play_widget, 'value'), (frame_slider, 'value'))
frame_slider.observe(update_preview, names='value')

def sync_play_range():
    n = max(len(frames) - 1, 0)
    play_widget.max = n
    frame_slider.max = n
    play_widget.interval = int(1000 / fps)
    if frames:
        preview_image.value = frame_to_png_bytes(frames[0])

def on_fps_change2(change):
    play_widget.interval = int(1000 / change['new'])
fps_slider.observe(on_fps_change2, names='value')

btn_prepare_play = widgets.Button(description='▶ 准备播放预览', button_style='info')

def prepare_play(_):
    if not frames:
        status.value = '先添加几帧动画吧'
        return
    sync_play_range()
    status.value = '预览已就绪，点下面的播放按钮 ▶'

btn_prepare_play.on_click(prepare_play)

play_row = widgets.HBox([play_widget, frame_slider])

# =========================
# EXPORT
# =========================
def export_png(_):
    arr = canvas.get_image_data()
    img = Image.fromarray(arr.astype('uint8'), 'RGBA')
    path = 'canvas.png'
    img.save(path)
    status.value = f'已保存 {path}'
    if IN_COLAB:
        colab_files.download(path)

def export_gif(_):
    if not frames:
        status.value = '先添加几帧动画吧'
        return
    status.value = '正在生成 GIF…'
    rgb_frames = []
    for arr in frames:
        img = Image.fromarray(arr.astype('uint8'), 'RGBA').convert('RGB')
        rgb_frames.append(np.array(img))
    path = 'animation.gif'
    imageio.mimsave(path, rgb_frames, fps=fps)
    status.value = f'GIF 已导出为 {path}'
    if IN_COLAB:
        colab_files.download(path)

btn_export_png = widgets.Button(description='下载画布 (PNG)')
btn_export_gif = widgets.Button(description='导出动画 (GIF)', button_style='warning')
btn_export_png.on_click(export_png)
btn_export_gif.on_click(export_gif)

export_row = widgets.HBox([btn_export_png, btn_export_gif])

# =========================
# LAYOUT
# =========================
refresh_filmstrip()

ui = widgets.VBox([
    widgets.HTML('<h2>手绘动画台（Colab 版）</h2>'),
    widgets.HBox([status, frame_count_label]),
    color_row,
    widgets.HBox([brush_slider, fps_slider]),
    canvas,
    frame_ops_row,
    widgets.HTML('<b>胶片预览：</b>'),
    filmstrip_box,
    widgets.HTML('<b>播放预览（先点"准备播放预览"，再拖动/点击左侧的 ▶）：</b>'),
    btn_prepare_play,
    play_row,
    preview_image,
    export_row,
])

display(ui)
