"""
手绘动画台 - 本地桌面版 (Tkinter + Pillow)
在 VS Code / 任意本地 Python 环境中直接运行:

    pip install pillow
    python animation_studio_desktop.py

用鼠标在画布上作画，保存帧，播放预览，导出 GIF。
"""

import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageDraw, ImageTk

# =========================
# 配置
# =========================
CANVAS_SIZE = 600
THUMB_SIZE = 60
PALETTE = [
    "#171512", "#ffffff", "#c0392b", "#2b5fa8", "#3f8f4f",
    "#e0c22e", "#d98a2b", "#3aa6a0", "#9b4fb0", "#7a5230",
]

# =========================
# 应用主类
# =========================
class AnimationStudio:
    def __init__(self, root):
        self.root = root
        self.root.title("手绘动画台 · 桌面版")
        self.root.configure(bg="#171512")

        # ---- 状态 ----
        self.draw_color = "#171512"
        self.brush_size = 30
        self.fps = 6
        self.last_xy = None
        self.frames = []          # 保存的每一帧 (PIL.Image)
        self.thumb_refs = []      # 防止缩略图被垃圾回收
        self.play_win = None
        self.play_after_id = None
        self.play_index = 0

        # ---- 画布 + 一张同步的 PIL 图像(用于导出/截帧) ----
        self.pil_image = Image.new("RGB", (CANVAS_SIZE, CANVAS_SIZE), "white")
        self.pil_draw = ImageDraw.Draw(self.pil_image)

        self._build_layout()
        self._redraw_canvas_from_pil()

    # -----------------------------------------------------
    # 界面布局
    # -----------------------------------------------------
    def _build_layout(self):
        # 左侧工具栏
        rail = tk.Frame(self.root, bg="#171512", padx=14, pady=14)
        rail.grid(row=0, column=0, sticky="ns")

        tk.Label(rail, text="颜色", fg="#8f887a", bg="#171512",
                 font=("Helvetica", 10)).pack(anchor="w")
        color_grid = tk.Frame(rail, bg="#171512")
        color_grid.pack(anchor="w", pady=(2, 12))
        for i, c in enumerate(PALETTE):
            b = tk.Button(color_grid, bg=c, width=2, height=1, relief="ridge",
                          command=lambda c=c: self.set_color(c))
            b.grid(row=i // 5, column=i % 5, padx=2, pady=2)

        tk.Label(rail, text="画笔粗细", fg="#8f887a", bg="#171512",
                 font=("Helvetica", 10)).pack(anchor="w")
        self.brush_scale = tk.Scale(rail, from_=1, to=100, orient="horizontal",
                                     bg="#171512", fg="white", highlightthickness=0,
                                     troughcolor="#3a352c", command=self.on_brush_change)
        self.brush_scale.set(self.brush_size)
        self.brush_scale.pack(fill="x", pady=(2, 12))

        tk.Label(rail, text="帧操作", fg="#8f887a", bg="#171512",
                 font=("Helvetica", 10)).pack(anchor="w")
        self._tool_button(rail, "保存当前帧 → 加入胶片", self.add_frame)
        self._tool_button(rail, "取回上一帧内容", self.keep_frame)
        self._tool_button(rail, "删除最后一帧", self.delete_last_frame)
        self._tool_button(rail, "清空所有帧", self.clear_frames)
        self._tool_button(rail, "清空画布", self.clear_canvas)

        tk.Label(rail, text="播放速度 (帧/秒)", fg="#8f887a", bg="#171512",
                 font=("Helvetica", 10)).pack(anchor="w", pady=(12, 0))
        self.fps_scale = tk.Scale(rail, from_=1, to=24, orient="horizontal",
                                   bg="#171512", fg="white", highlightthickness=0,
                                   troughcolor="#3a352c", command=self.on_fps_change)
        self.fps_scale.set(self.fps)
        self.fps_scale.pack(fill="x", pady=(2, 12))

        tk.Label(rail, text="导出", fg="#8f887a", bg="#171512",
                 font=("Helvetica", 10)).pack(anchor="w")
        self._tool_button(rail, "▶ 播放动画预览", self.play_animation)
        self._tool_button(rail, "下载当前画布 (PNG)", self.save_png)
        self._tool_button(rail, "导出动画 (GIF)", self.export_gif)

        # 中间画布
        stage = tk.Frame(self.root, bg="#0f0e0c")
        stage.grid(row=0, column=1, sticky="nsew")

        self.frame_count_label = tk.Label(stage, text="胶片长度: 0 帧",
                                           fg="#8f887a", bg="#0f0e0c",
                                           font=("Helvetica", 10))
        self.frame_count_label.pack(pady=(10, 4))

        self.canvas = tk.Canvas(stage, width=CANVAS_SIZE, height=CANVAS_SIZE,
                                 bg="white", highlightthickness=0, cursor="crosshair")
        self.canvas.pack(padx=20, pady=10)
        self.canvas.bind("<Button-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_move)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)

        self.status_label = tk.Label(stage, text="就绪", fg="#8f887a", bg="#0f0e0c",
                                      font=("Helvetica", 10))
        self.status_label.pack(pady=(0, 6))

        # 底部胶片条
        strip_wrap = tk.Frame(self.root, bg="#2a2723")
        strip_wrap.grid(row=1, column=0, columnspan=2, sticky="ew")
        self.filmstrip = tk.Frame(strip_wrap, bg="#2a2723")
        self.filmstrip.pack(fill="x", padx=10, pady=8)

        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)

    def _tool_button(self, parent, text, command):
        b = tk.Button(parent, text=text, command=command, anchor="w",
                      bg="#171512", fg="white", activebackground="#3a352c",
                      activeforeground="#d98a2b", relief="flat", bd=0,
                      font=("Helvetica", 10), padx=4, pady=5)
        b.pack(fill="x")
        return b

    # -----------------------------------------------------
    # 颜色 / 画笔 / 帧率
    # -----------------------------------------------------
    def set_color(self, color):
        self.draw_color = color

    def on_brush_change(self, value):
        self.brush_size = int(value)

    def on_fps_change(self, value):
        self.fps = int(value)

    # -----------------------------------------------------
    # 绘图
    # -----------------------------------------------------
    def on_mouse_down(self, event):
        self.last_xy = (event.x, event.y)
        self._dot(event.x, event.y)

    def on_mouse_move(self, event):
        x, y = event.x, event.y
        if self.last_xy:
            self._line(self.last_xy[0], self.last_xy[1], x, y)
        self._dot(x, y)
        self.last_xy = (x, y)

    def on_mouse_up(self, event):
        self.last_xy = None

    def _dot(self, x, y):
        r = self.brush_size / 2
        # tk 画布上显示
        self.canvas.create_oval(x - r, y - r, x + r, y + r,
                                 fill=self.draw_color, outline=self.draw_color)
        # 同步到 PIL 图像，用于截帧/导出
        self.pil_draw.ellipse([x - r, y - r, x + r, y + r], fill=self.draw_color)

    def _line(self, x0, y0, x1, y1):
        self.canvas.create_line(x0, y0, x1, y1, fill=self.draw_color,
                                 width=self.brush_size, capstyle="round",
                                 joinstyle="round")
        self.pil_draw.line([x0, y0, x1, y1], fill=self.draw_color,
                            width=self.brush_size, joint="curve")

    def clear_canvas(self):
        self.canvas.delete("all")
        self.pil_image = Image.new("RGB", (CANVAS_SIZE, CANVAS_SIZE), "white")
        self.pil_draw = ImageDraw.Draw(self.pil_image)
        self.status_label.config(text="画布已清空")

    def _redraw_canvas_from_pil(self):
        self.tk_image = ImageTk.PhotoImage(self.pil_image)
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor="nw", image=self.tk_image)

    # -----------------------------------------------------
    # 帧操作
    # -----------------------------------------------------
    def add_frame(self):
        self.frames.append(self.pil_image.copy())
        self.clear_canvas()
        self._refresh_filmstrip()
        self.status_label.config(text=f"已保存为第 {len(self.frames)} 帧")

    def keep_frame(self):
        if not self.frames:
            self.status_label.config(text="还没有帧可以取回")
            return
        self.pil_image = self.frames[-1].copy()
        self.pil_draw = ImageDraw.Draw(self.pil_image)
        self._redraw_canvas_from_pil()
        self.status_label.config(text="已取回上一帧")

    def delete_last_frame(self):
        if not self.frames:
            self.status_label.config(text="没有可删除的帧")
            return
        self.frames.pop()
        self._refresh_filmstrip()
        self.status_label.config(text="已删除最后一帧")

    def clear_frames(self):
        if not self.frames:
            return
        self.frames.clear()
        self._refresh_filmstrip()
        self.status_label.config(text="已清空所有帧")

    def _refresh_filmstrip(self):
        for w in self.filmstrip.winfo_children():
            w.destroy()
        self.thumb_refs.clear()

        if not self.frames:
            tk.Label(self.filmstrip, text="还没有帧 — 画点什么，然后点击「保存当前帧」把它放进胶片里。",
                     fg="#5c5748", bg="#2a2723", font=("Helvetica", 9)).pack(side="left")
        else:
            for i, frame in enumerate(self.frames):
                thumb = frame.copy()
                thumb.thumbnail((THUMB_SIZE, THUMB_SIZE))
                tk_thumb = ImageTk.PhotoImage(thumb)
                self.thumb_refs.append(tk_thumb)  # 防止被回收
                cell = tk.Frame(self.filmstrip, bg="#2a2723")
                cell.pack(side="left", padx=4)
                tk.Label(cell, image=tk_thumb, bg="white",
                         relief="solid", bd=1).pack()
                tk.Label(cell, text=str(i + 1), fg="#8f887a", bg="#2a2723",
                         font=("Helvetica", 8)).pack()

        self.frame_count_label.config(text=f"胶片长度: {len(self.frames)} 帧")

    # -----------------------------------------------------
    # 播放预览
    # -----------------------------------------------------
    def play_animation(self):
        if not self.frames:
            self.status_label.config(text="先添加几帧动画吧")
            return

        if self.play_win is not None and self.play_win.winfo_exists():
            self.play_win.destroy()

        self.play_win = tk.Toplevel(self.root)
        self.play_win.title("动画预览")
        self.play_canvas = tk.Canvas(self.play_win, width=CANVAS_SIZE, height=CANVAS_SIZE,
                                      bg="white", highlightthickness=0)
        self.play_canvas.pack()
        self.play_label = tk.Label(self.play_win, text="")
        self.play_label.pack(pady=4)
        tk.Button(self.play_win, text="✕ 关闭预览",
                  command=self._stop_play).pack(pady=(0, 8))

        self.play_win.protocol("WM_DELETE_WINDOW", self._stop_play)
        self.play_index = 0
        self._play_tick()

    def _play_tick(self):
        if self.play_win is None or not self.play_win.winfo_exists():
            return
        frame = self.frames[self.play_index]
        self.play_tk_image = ImageTk.PhotoImage(frame)
        self.play_canvas.delete("all")
        self.play_canvas.create_image(0, 0, anchor="nw", image=self.play_tk_image)
        self.play_label.config(text=f"帧 {self.play_index + 1} / {len(self.frames)}")
        self.play_index = (self.play_index + 1) % len(self.frames)
        delay_ms = int(1000 / max(self.fps, 1))
        self.play_after_id = self.root.after(delay_ms, self._play_tick)

    def _stop_play(self):
        if self.play_after_id is not None:
            self.root.after_cancel(self.play_after_id)
            self.play_after_id = None
        if self.play_win is not None:
            self.play_win.destroy()
            self.play_win = None

    # -----------------------------------------------------
    # 导出
    # -----------------------------------------------------
    def save_png(self):
        path = "canvas.png"
        self.pil_image.save(path)
        self.status_label.config(text=f"已保存 {path}")
        messagebox.showinfo("已保存", f"当前画布已保存为 {path}")

    def export_gif(self):
        if not self.frames:
            self.status_label.config(text="先添加几帧动画吧")
            return
        path = "animation.gif"
        duration_ms = int(1000 / max(self.fps, 1))
        self.frames[0].save(
            path,
            save_all=True,
            append_images=self.frames[1:],
            duration=duration_ms,
            loop=0,
        )
        self.status_label.config(text=f"GIF 已导出为 {path}")
        messagebox.showinfo("导出完成", f"动画已导出为 {path}")


# =========================
# 启动
# =========================
if __name__ == "__main__":
    root = tk.Tk()
    app = AnimationStudio(root)
    root.mainloop()
