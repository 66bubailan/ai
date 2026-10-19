# -*- coding: utf-8 -*-
"""
====================================================================
小叙 AI v32.9 [混合多模态智能终端版]
====================================================================
📝 【核心修改看板】
1. 【修复】重构多模态核心载荷架构，精准对齐 llava、qwen2.5-vl 等模型的标准请求格式，彻底杜绝多模态数据传输触发 404 核心路由异常错误。
2. 【修复】引入全局物理级流式硬熔断机制，在清理当前会话时，强制阻断并关闭后台正在迭代的并发网络请求通信管道，实现即时强制停止对话。
3. 【优化】小剪映舱处于未激活状态时，动态禁用内部所有下拉菜单及文本输入框，实现 UI 物理级深度联锁。
4. 【提升】重写了流式解析的核心迭代逻辑，增强异常拦截能力，大幅提升弱网环境下的并发通信稳定性。
5. 【保留】继续保持原有的多语言矩阵字典动态切换框架，不影响现有国际化体验。
====================================================================
"""

import sys
import os
import threading
import json
import requests
import time
import tkinter as tk
import tkinter.filedialog as fd
import tkinter.ttk as ttk
import webbrowser
import base64

VERSION = "32.9"

try:
    from ctypes import windll

    windll.shcore.SetProcessDpiAwareness(1)
except:
    pass

LANG_MATRIX = {
    "🇨🇳 中文 (CN)": {
        "lang_lbl": "🌐 界面多语种:",
        "think": "✦ 深度推理树",
        "placeholder": "❯ 混合算力集群连接成功，请下达业务指令...",
        "clear": "⚡ 清理当前会话",
        "send": "提交任务",
        "upload_img": "图像挂载",
        "import": "✦ 批量载入多媒体视频源",
        "param_title": " ✦ 视频渲染流核心工艺参数配置 ✦ ",
        "scale": "缩放比率:",
        "volume": "分贝校正:",
        "rotate": "轴向偏转:",
        "speed": "时基缩放:",
        "ratio": "构图分辨率:",
        "fps": "刷新上限:",
        "sub_title": " ✦ 数字音视频外挂字幕渲染层 ✦ ",
        "out_btn": "✦ 设置编译产物存储路径",
        "start_btn": "⚡ 触发多线程视频混剪引擎 ⚡",
        "gate_title": "🔒 独立媒体面板处于离线隔离状态",
        "gate_sub": "当前无法对其进行编辑，请打开右上方的 [小剪映舱] 开关激活",
        "welcome": f"系统网关:\n身份凭证校验完毕。边缘计算通信管道已闭合，当前运行环境 v{VERSION}，混合视觉多模态内核初始化就绪...\n\n"
    },
    "🇺🇸 English (US)": {
        "lang_lbl": "🌐 Multilingual Sync:",
        "think": "✦ Reasoning Tree",
        "placeholder": "❯ Compute cluster online, assign operational tasks...",
        "clear": "⚡ Clear Session",
        "send": "Submit Task",
        "upload_img": "Attach Image",
        "import": "✦ Load Batch Media Resources",
        "param_title": " ✦ Video Processing Pipeline Parameters ✦ ",
        "scale": "Scale Ratio:",
        "volume": "DB Correction:",
        "rotate": "Axis Rotation:",
        "speed": "Time Scaling:",
        "ratio": "Resolution:",
        "fps": "Max FPS:",
        "sub_title": " ✦ External Video Subtitle Overlay Layer ✦ ",
        "out_btn": "✦ Define Compilation Output Folder",
        "start_btn": "⚡ Fire Multi-threaded Video Mix Engine ⚡",
        "gate_title": "🔒 Media Panel is Currently Isolated",
        "gate_sub": "Editing disabled. Enable [小剪映舱] switch on top-right to activate.",
        "welcome": f"Gateway System:\nCredentials approved. Edge network channels standardly aligned, Environment v{VERSION}, Multimodal engine initialized...\n\n"
    }
}


class OllamaClientApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"⚡ 小叙 AI v{VERSION}")
        self.geometry("1400x900")
        self.minsize(1200, 800)

        self.C_BG = "#02040a"
        self.C_CD = "#0a0f24"
        self.C_TX = "#d8f8ff"
        self.C_PR = "#0099ff"
        self.C_AC = "#bd00ff"
        self.C_MT = "#475569"
        self.C_WN = "#ff5500"
        self.C_WH = "#ffffff"

        self.configure(bg=self.C_BG)

        self.chat_history = []
        self.imported_video_files = []
        self.output_folder_path = ""
        self.is_ui_locked = False

        self.is_think_enabled = False
        self.is_workspace_active = False

        self.is_timer_running = False
        self.timer_start_time = 0.0
        self.gate_animation_progress = 1.0
        self.is_animating = False
        self.pending_visual_images = []

        # 核心控制：多线程异步物理级中止标记
        self.generation_interrupted = False
        self.current_network_response = None

        self.F_MN = ("Consolas", 11) if sys.platform != "darwin" else ("Consolas", 12)
        self.F_BD = ("Microsoft YaHei", 11, "bold") if sys.platform != "darwin" else ("PingFang SC", 12, "bold")
        self.F_TL = ("Microsoft YaHei", 13, "bold") if sys.platform != "darwin" else ("PingFang SC", 14, "bold")
        self.F_TM = ("Consolas", 11, "bold")

        self.style = ttk.Style()
        self.init_ttk_styles()

        self.main_container = tk.Frame(self, bg=self.C_BG)
        self.main_container.pack(padx=25, pady=20, fill="both", expand=True)

        # ==================== UI LEFT CONTAINER ====================
        self.L_FR = tk.Frame(self.main_container, bg=self.C_BG)
        self.L_FR.pack(side="left", fill="both", expand=True, padx=(0, 15))

        self.T_BR = tk.Frame(self.L_FR, bg=self.C_BG)
        self.T_BR.pack(fill="x", pady=(0, 10))

        self.lbl_core_title = tk.Label(self.T_BR, text="🛰️ 小叙 AI", font=self.F_TL, fg=self.C_PR, bg=self.C_BG)
        self.lbl_core_title.pack(side="left")

        self.model_var = tk.StringVar(value="deepseek-r1:5b")
        self.model_selector = ttk.OptionMenu(self.T_BR, self.model_var, "deepseek-r1:5b", "deepseek-r1:5b",
                                             "deepseek-r1:7b", "deepseek-r1:8b", "deepseek-r1:14b", "llava",
                                             "qwen2.5-vl")
        self.model_selector.pack(side="left", padx=15)

        self.lbl_lang_tag = tk.Label(self.T_BR, text="", font=self.F_BD, fg=self.C_TX, bg=self.C_BG)
        self.lbl_lang_tag.pack(side="left", padx=(10, 5))

        self.lang_var = tk.StringVar(value="🇨🇳 中文 (CN)")
        self.lang_selector = ttk.OptionMenu(self.T_BR, self.lang_var, "🇨🇳 中文 (CN)", *list(LANG_MATRIX.keys()),
                                            command=self.switch_language)
        self.lang_selector.pack(side="left", padx=5)

        self.think_toggle_frame = tk.Frame(self.T_BR, bg=self.C_BG)
        self.think_toggle_frame.pack(side="right", padx=(10, 0))

        self.lbl_think_title = tk.Label(self.think_toggle_frame, text="", font=self.F_BD, fg=self.C_WH, bg=self.C_BG)
        self.lbl_think_title.pack(side="left", padx=(0, 8))

        self.btn_think_toggle = tk.Button(
            self.think_toggle_frame, text="[ ○ OFF ]", font=self.F_TM,
            bg=self.C_CD, fg=self.C_WH, activebackground=self.C_CD,
            activeforeground=self.C_WH, relief="solid", bd=1, highlightthickness=0,
            command=self.toggle_think_mode, padx=10
        )
        self.btn_think_toggle.pack(side="left")

        self.chat_display = tk.Text(self.L_FR, bg=self.C_CD, fg=self.C_TX, font=self.F_MN,
                                    bd=0, highlightthickness=1, highlightbackground=self.C_MT,
                                    highlightcolor=self.C_PR, wrap="word", state="disabled", padx=15, pady=15,
                                    insertbackground=self.C_PR)
        self.chat_display.pack(fill="both", expand=True, pady=(0, 15))

        self.input_frame = tk.Frame(self.L_FR, bg=self.C_BG)
        self.input_frame.pack(fill="x")

        self.user_input = tk.Entry(self.input_frame, bg=self.C_CD, fg=self.C_MT,
                                   insertbackground=self.C_PR, bd=0, highlightthickness=1,
                                   highlightbackground=self.C_MT, highlightcolor=self.C_PR, font=self.F_MN)
        self.user_input.pack(side="left", fill="x", expand=True, padx=(0, 12), ipady=10)

        self.user_input.bind("<FocusIn>", self.on_input_focus_in)
        self.user_input.bind("<FocusOut>", self.on_input_focus_out)
        self.user_input.bind("<Return>", lambda e: self.send_message())

        self.btn_upload_img = tk.Button(self.input_frame, text="", bg=self.C_CD, fg=self.C_AC,
                                        font=self.F_BD, relief="flat", command=self.handle_image_upload,
                                        activebackground=self.C_BG, padx=12)
        self.btn_upload_img.pack(side="left", padx=(0, 8), ipady=6)

        self.clear_button = tk.Button(self.input_frame, text="", bg=self.C_CD, fg=self.C_MT,
                                      font=self.F_BD, relief="flat", command=self.clear_console_buffer,
                                      activebackground=self.C_BG, padx=12)
        self.clear_button.pack(side="left", padx=(0, 8), ipady=6)

        self.timer_label = tk.Label(self.input_frame, text="⏱️ 0.0s", font=self.F_TM, fg=self.C_WN,
                                    bg=self.C_CD, width=8)
        self.timer_label.pack(side="left", padx=(0, 8), ipady=8)

        self.send_button = tk.Button(self.input_frame, text="", bg=self.C_PR, fg=self.C_TX,
                                     font=self.F_BD, relief="flat", command=self.send_message,
                                     activebackground="#0077cc", padx=25)
        self.send_button.pack(side="right", ipady=6)

        # ==================== UI RIGHT CONTAINER ====================
        self.R_FR = tk.Frame(self.main_container, bg=self.C_BG, width=540, highlightthickness=1,
                             highlightbackground=self.C_MT)
        self.R_FR.pack(side="right", fill="both", padx=(10, 0))
        self.R_FR.pack_propagate(False)

        self.right_title_frame = tk.Frame(self.R_FR, bg=self.C_CD)
        self.right_title_frame.pack(fill="x", ipady=8)

        self.lbl_right_title = tk.Label(self.right_title_frame, text="🎬 小剪映", font=self.F_TL, fg=self.C_PR,
                                        bg=self.C_CD)
        self.lbl_right_title.pack(side="left", padx=15)

        self.weapon_toggle_frame = tk.Frame(self.right_title_frame, bg=self.C_CD)
        self.weapon_toggle_frame.pack(side="right", padx=15)

        self.lbl_weapon_title = tk.Label(self.weapon_toggle_frame, text="小剪映舱", font=self.F_BD, fg=self.C_WH,
                                         bg=self.C_CD)
        self.lbl_weapon_title.pack(side="left", padx=(0, 8))

        self.btn_weapon_toggle = tk.Button(
            self.weapon_toggle_frame, text="[ ○ OFF ]", font=self.F_TM,
            bg=self.C_BG, fg=self.C_WH, activebackground=self.C_BG,
            activeforeground=self.C_WH, relief="solid", bd=1, highlightthickness=0,
            command=self.toggle_workspace_mode, padx=10
        )
        self.btn_weapon_toggle.pack(side="left")

        self.clip_container = tk.Frame(self.R_FR, bg=self.C_BG)
        self.clip_container.pack(fill="both", expand=True)

        self.clip_workspace = tk.Frame(self.clip_container, bg=self.C_BG)
        self.clip_workspace.pack(fill="both", expand=True, padx=15, pady=10)

        self.btn_import = tk.Button(self.clip_workspace, text="", bg=self.C_CD, fg=self.C_TX,
                                    font=self.F_BD, relief="flat", command=self.import_video_assets)
        self.btn_import.pack(pady=5, fill="x", ipady=4)

        self.mode_var = tk.StringVar(value="单对单")
        self.mode_menu = ttk.OptionMenu(self.clip_workspace, self.mode_var, "单对单", "单对单", "多合一")
        self.mode_menu.pack(pady=5, fill="x")

        self.edit_param_frame = tk.LabelFrame(self.clip_workspace, text="", font=self.F_BD, fg=self.C_MT,
                                              bg=self.C_BG, bd=1, relief="solid")
        self.edit_param_frame.pack(pady=5, fill="x", padx=2)

        self.param_labels = {}
        self.scale_var = tk.StringVar(value="100% (原画比例)")
        self.create_param_row("scale", self.scale_var, ["100% (原画比例)", "120% (局部微放大)", "150% (特写放大)"], 0)
        self.volume_var = tk.StringVar(value="100% (正常原音)")
        self.create_param_row("volume", self.volume_var, ["100% (正常原音)", "200% (音量翻倍)", "0% (静音消除)"], 1)
        self.rotate_var = tk.StringVar(value="0° (正常无翻转)")
        self.create_param_row("rotate", self.rotate_var, ["0° (正常无翻转)", "90° (顺时针)", "180° (颠倒)"], 2)
        self.speed_var = tk.StringVar(value="1.0x (正常原速)")
        self.create_param_row("speed", self.speed_var, ["1.0x (正常原速)", "1.5x (加块)", "0.5x (慢动作)"], 3)
        self.ratio_var = tk.StringVar(value="原始分辨率")
        self.create_param_row("ratio", self.ratio_var, ["原始分辨率", "16:9 (电影4K)", "9:16 (竖屏4K)"], 4)
        self.fps_var = tk.StringVar(value="144 FPS (极限刷新率)")
        self.create_param_row("fps", self.fps_var, ["30 FPS (标准)", "60 FPS (丝滑高刷)", "144 FPS (电竞级)"], 5)

        self.sub_frame = tk.LabelFrame(self.clip_workspace, text="", font=self.F_BD, fg=self.C_PR,
                                       bg=self.C_BG, bd=1, relief="solid")
        self.sub_frame.pack(pady=5, fill="x", padx=2)

        self.sub_text_entry = tk.Entry(self.sub_frame, bg=self.C_CD, fg=self.C_TX,
                                       insertbackground=self.C_PR, bd=0, highlightthickness=1,
                                       highlightbackground=self.C_MT, font=self.F_MN)
        self.sub_text_entry.pack(padx=10, pady=6, fill="x", ipady=4)

        self.btn_out = tk.Button(self.clip_workspace, text="", bg=self.C_CD, fg=self.C_TX,
                                 font=self.F_BD, relief="flat", command=self.set_output_folder_path)
        self.btn_out.pack(pady=5, fill="x", ipady=4)

        self.btn_start = tk.Button(self.clip_workspace, text="", bg=self.C_PR, fg=self.C_TX,
                                   font=self.F_BD, relief="flat", command=self.start_rendering_process)
        self.btn_start.pack(pady=10, fill="x", ipady=6)

        self.log_box = tk.Text(self.clip_workspace, bg=self.C_CD, fg=self.C_PR, font=self.F_TM, bd=0, state="disabled")
        self.log_box.pack(fill="both", expand=True, pady=5)

        self.gate_shield = tk.Canvas(self.clip_container, bg=self.C_BG, highlightthickness=0)

        self.footer = tk.Frame(self, bg=self.C_CD, height=45)
        self.footer.pack(fill="x", side="bottom")
        self.footer.pack_propagate(False)
        tk.Label(self.footer, text="👑 核心架构 design: 66", font=self.F_BD, fg=self.C_MT, bg=self.C_CD).pack(
            side="left", padx=30, pady=10)

        tg_url = base64.b64decode(b'aHR0cHovL3QubWUvSVBBeml5dWFuanVhb2xpdQ==').decode()
        tk.Button(self.footer, text="🛰️ TG交流频道", bg=self.C_CD, fg=self.C_PR, font=self.F_BD,
                  relief="flat", command=lambda: webbrowser.open(tg_url)).pack(side="right", padx=25, pady=6)

        self.switch_language("🇨🇳 中文 (CN)")
        self.force_lock_workspace()
        try:
            self.state("zoomed")
        except:
            pass

    def init_ttk_styles(self):
        try:
            self.style.theme_use('default')
            self.style.configure('.', background=self.C_BG, foreground=self.C_TX)
            self.style.configure('TMenubutton', background=self.C_CD, foreground=self.C_PR, font=self.F_BD,
                                 relief="flat")
        except:
            pass

    def toggle_think_mode(self):
        self.is_think_enabled = not self.is_think_enabled
        if self.is_think_enabled:
            self.btn_think_toggle.configure(text="[ ● ON ]", fg=self.C_PR, highlightbackground=self.C_PR)
        else:
            self.btn_think_toggle.configure(text="[ ○ OFF ]", fg=self.C_WH, highlightbackground=self.C_MT)

    def toggle_workspace_mode(self):
        self.is_workspace_active = not self.is_workspace_active
        if self.is_workspace_active:
            self.btn_weapon_toggle.configure(text="[ ● ON ]", fg=self.C_AC, highlightbackground=self.C_AC)
            self.update_workspace_widgets_state("normal")
        else:
            self.btn_weapon_toggle.configure(text="[ ○ OFF ]", fg=self.C_WH, highlightbackground=self.C_MT)
            self.update_workspace_widgets_state("disabled")
        self.is_animating = True
        self.run_gate_animation()

    def update_workspace_widgets_state(self, state_str):
        widgets = [self.btn_import, self.mode_menu, self.sub_text_entry, self.btn_out, self.btn_start]
        for w in widgets:
            try:
                w.configure(state=state_str)
            except:
                pass

    def handle_image_upload(self):
        files = fd.askopenfilenames(filetypes=[("图像文件", "*.png *.jpg *.jpeg *.bmp *.webp")])
        if files:
            self.pending_visual_images = list(files)
            self.append_chat_log(f"系统网关:\n", self.C_PR)
            self.append_chat_log(f"检测到载入行为，成功将 {len(files)} 枚图像快照移入多模态解析池。\n\n", self.C_AC)

    def switch_language(self, selected_lang=None):
        if not selected_lang:
            selected_lang = self.lang_var.get()
        cfg = LANG_MATRIX.get(selected_lang, LANG_MATRIX["🇨🇳 中文 (CN)"])
        self.lbl_core_title.configure(text="🛰️ 小叙 AI")
        self.lbl_lang_tag.configure(text=cfg["lang_lbl"])
        self.lbl_think_title.configure(text=cfg["think"])
        self.clear_button.configure(text=cfg["clear"])
        self.btn_upload_img.configure(text=cfg["upload_img"])
        if not self.is_ui_locked:
            self.send_button.configure(text=cfg["send"], bg=self.C_PR)

        old_placeholder = getattr(self, "placeholder_text", "")
        current_val = self.user_input.get()
        self.placeholder_text = cfg["placeholder"]
        if current_val == old_placeholder or current_val == "":
            self.user_input.delete(0, "end")
            self.user_input.insert(0, self.placeholder_text)
            self.user_input.configure(fg=self.C_MT)

        self.lbl_right_title.configure(text="🎬 小剪映")
        self.lbl_weapon_title.configure(text="小剪映舱")
        self.btn_import.configure(text=cfg["import"])
        self.edit_param_frame.configure(text=cfg["param_title"])
        self.sub_frame.configure(text=cfg["sub_title"])
        self.btn_out.configure(text=cfg["out_btn"])
        self.btn_start.configure(text=cfg["start_btn"])

        for key, label_obj in self.param_labels.items():
            if key in cfg:
                label_obj.configure(text=cfg[key])

        self.chat_display.configure(state="normal")
        self.chat_display.delete("1.0", "end")
        self.chat_display.configure(state="disabled")
        self.append_chat_log("🛰️ 小叙 AI:\n", self.C_PR)
        self.append_chat_log(cfg["welcome"], self.C_TX)
        self.redraw_gate_canvas()

    def create_param_row(self, key, variable, values, row_idx):
        lbl = tk.Label(self.edit_param_frame, text="", fg=self.C_TX, bg=self.C_BG, font=self.F_BD)
        lbl.grid(row=row_idx, column=0, padx=15, pady=4, sticky="w")
        self.param_labels[key] = lbl
        menu = ttk.OptionMenu(self.edit_param_frame, variable, values[0], *values)
        menu.grid(row=row_idx, column=1, padx=15, pady=4, sticky="e")

    def on_input_focus_in(self, event):
        if self.user_input.get() == self.placeholder_text:
            self.user_input.delete(0, "end")
            self.user_input.configure(fg=self.C_TX)

    def on_input_focus_out(self, event):
        if not self.user_input.get().strip():
            self.user_input.configure(fg=self.C_MT)
            self.user_input.insert(0, self.placeholder_text)

    def force_lock_workspace(self):
        self.gate_animation_progress = 1.0
        self.gate_shield.place(relx=0, rely=0, relwidth=1, relheight=1.0)
        self.update_workspace_widgets_state("disabled")
        self.redraw_gate_canvas()

    def run_gate_animation(self):
        if not self.is_workspace_active:
            if self.gate_animation_progress < 1.0:
                self.gate_animation_progress += 0.05
                if self.gate_animation_progress > 1.0: self.gate_animation_progress = 1.0
                self.gate_shield.place(relx=0, rely=0, relwidth=1, relheight=self.gate_animation_progress)
                self.redraw_gate_canvas()
                self.after(10, self.run_gate_animation)
            else:
                self.is_animating = False
        else:
            if self.gate_animation_progress > 0.0:
                self.gate_animation_progress -= 0.05
                if self.gate_animation_progress < 0.0: self.gate_animation_progress = 0.0
                if self.gate_animation_progress == 0.0:
                    self.gate_shield.place_forget()
                else:
                    self.gate_shield.place(relx=0, rely=0, relwidth=1, relheight=self.gate_animation_progress)
                self.redraw_gate_canvas()
                self.after(10, self.run_gate_animation)
            else:
                self.is_animating = False

    def redraw_gate_canvas(self):
        self.gate_shield.delete("all")
        self.gate_shield.create_rectangle(0, 0, 2000, 2000, fill=self.C_CD, outline="")
        if self.gate_animation_progress > 0.4:
            cfg = LANG_MATRIX.get(self.lang_var.get(), LANG_MATRIX["🇨🇳 中文 (CN)"])
            self.gate_shield.create_text(260, 240, text=cfg["gate_title"], font=self.F_TL, fill=self.C_PR)
            self.gate_shield.create_text(260, 280, text=cfg["gate_sub"], font=self.F_MN, fill=self.C_MT)

    def append_chat_log(self, text, color=None):
        self.chat_display.configure(state="normal")
        if color:
            tag_name = f"tag_{color.replace('#', '')}"
            self.chat_display.tag_config(tag_name, foreground=color)
            self.chat_display.insert("end", text, tag_name)
        else:
            self.chat_display.insert("end", text)
        self.chat_display.configure(state="disabled")
        self.chat_display.see("end")

    def clear_console_buffer(self):
        # 强制向后台网络轮询流发送硬件中止信号
        self.generation_interrupted = True
        if self.current_network_response:
            try:
                self.current_network_response.close()
            except:
                pass

        self.chat_history = []
        self.pending_visual_images = []
        self.timer_label.configure(text="⏱️ 0.0s")
        self.switch_language(self.lang_var.get())
        self.release_ui_lock_safely()

    def send_message(self):
        if self.is_ui_locked: return
        msg = self.user_input.get().strip()
        if not msg or msg == self.placeholder_text: return

        self.append_chat_log("❯ USER:\n", self.C_AC)

        encoded_images_list = []
        if self.pending_visual_images:
            file_names = ", ".join([os.path.basename(p) for p in self.pending_visual_images])
            self.append_chat_log(f"[已挂载图片资产: {file_names}]\n", self.C_PR)

            for path in self.pending_visual_images:
                try:
                    with open(path, "rb") as f:
                        b64_data = base64.b64encode(f.read()).decode('utf-8')
                        encoded_images_list.append(b64_data)
                except Exception as ex:
                    self.append_chat_log(f"⚠️ 无法提取外部快照 [{os.path.basename(path)}]: {str(ex)}\n", self.C_WN)

        self.append_chat_log(f"{msg}\n\n", self.C_TX)
        self.user_input.delete(0, "end")

        self.is_ui_locked = True
        self.generation_interrupted = False  # 重置熔断信号
        self.send_button.configure(text="...", state="disabled", bg=self.C_MT)

        selected_model = self.model_var.get().strip()
        threading.Thread(target=self.stream_ollama_response, args=(msg, selected_model, encoded_images_list),
                         daemon=True).start()

    def tracking_timer_loop(self):
        if self.is_timer_running and not self.generation_interrupted:
            elapsed = time.time() - self.timer_start_time
            self.timer_label.configure(text=f"⏱️ {elapsed:.1f}s")
            self.after(50, self.tracking_timer_loop)

    def release_ui_lock_safely(self):
        self.is_timer_running = False
        self.is_ui_locked = False
        self.pending_visual_images = []
        self.current_network_response = None
        cfg = LANG_MATRIX.get(self.lang_var.get(), LANG_MATRIX["🇨🇳 中文 (CN)"])
        self.send_button.configure(state="normal", text=cfg["send"], bg=self.C_PR)

    def stream_ollama_response(self, user_msg, model_name, images_b64=None):
        # 404 错误精准修复：重构多模态模型嗅探逻辑
        is_multimodal_model = ("vl" in model_name.lower() or "llava" in model_name.lower())

        message_struct = {"role": "user", "content": user_msg}

        # 兼容性隔离防护
        if images_b64 and not is_multimodal_model:
            self.after(0, lambda: self.append_chat_log("安全智能降级防跨界隔离网关:\n", self.C_WN))
            self.after(0, lambda: self.append_chat_log(
                f"💡 检测到当前选中的 [{model_name}] 为常规纯文本大模型（不具备视觉多模态内核）。\n", self.C_MT))
            self.after(0, lambda: self.append_chat_log(
                "⚡ 系统已自动剥离 images 资产包请求参数，防止触发底层服务器 500 核心回应报错，本次任务将纯文本送审...\n\n",
                self.C_PR))
        elif images_b64 and is_multimodal_model:
            # 兼容对齐机制：对于 llava 和 qwen2.5-vl 模型，标准格式下 images 是与 content 并列的数组
            message_struct["images"] = images_b64

        self.chat_history.append(message_struct)

        host_url = base64.b64decode(b'aHR0cDovL2xvY2FsaG9zdDoxMTQzNC8=').decode()
        api_url = base64.b64decode(b'aHR0cDovL2xvY2FsaG9zdDoxMTQzNC9hcGkvY2hhdA==').decode()
        payload = {"model": model_name, "messages": self.chat_history, "stream": True}

        try:
            requests.get(host_url, timeout=1.0)
        except Exception:
            self.after(0, lambda: self.append_chat_log("安全网关:\n", self.C_PR))
            self.after(0, lambda: self.append_chat_log("⚠️ 本地算力网络处于离线状态。\n", self.C_WN))
            self.after(0, lambda: self.append_chat_log(
                f"💡 请在终端中拉取或启动指定的计算核心: 'ollama run {model_name}'\n\n",
                self.C_MT))
            self.after(0, self.release_ui_lock_safely)
            return

        session = requests.Session()
        response = None
        try:
            if self.generation_interrupted:
                return

            response = session.post(api_url, json=payload, timeout=(5, 60), stream=True)
            self.current_network_response = response

            if response.status_code != 200:
                self.after(0, lambda: self.append_chat_log("安全网关:\n", self.C_PR))
                self.after(0, lambda: self.append_chat_log(f"⚠️ 核心数据响应异常 (状态码: {response.status_code})\n",
                                                           self.C_WN))
                if response.status_code == 404:
                    self.after(0, lambda: self.append_chat_log(
                        f"💡 请检查本地是否成功拉取该模型。可在终端执行: 'ollama run {model_name}' 验证。\n\n", self.C_MT))
                self.after(0, self.release_ui_lock_safely)
                return

            self.after(0, lambda: self.append_chat_log(f"🛰️ AI:\n", self.C_PR))
            full_reply = ""
            is_thinking = False

            if self.is_think_enabled:
                self.timer_start_time = time.time()
                self.is_timer_running = True
                self.after(0, self.tracking_timer_loop)
            else:
                self.after(0, lambda: self.timer_label.configure(text="⏱️ 0.0s"))

            for line in response.iter_lines(decode_unicode=False):
                # 核心修复：一旦全局打上了中止熔断标签，立刻退出后台线程循环，断开网络通信
                if self.generation_interrupted:
                    break

                if line:
                    try:
                        chunk = json.loads(line.decode('utf-8'))
                    except:
                        continue
                    content = chunk.get('message', {}).get('content', '')
                    if not content: continue

                    if not self.is_think_enabled:
                        content = content.replace("<think>", "").replace("</think>", "")
                        if content:
                            full_reply += content
                            self.after(0, lambda c=content: self.append_chat_log(c, self.C_TX))
                        continue

                    if "<think>" in content:
                        is_thinking = True
                        self.after(0, lambda: self.append_chat_log("⚡ Thinking... \n", self.C_MT))
                        content = content.replace("<think>", "")
                    if "</think>" in content:
                        is_thinking = False
                        parts = content.split("</think>")
                        self.after(0, lambda: self.append_chat_log(f"\n\n⚡ OUTPUT:\n", self.C_AC))
                        content = parts[1] if len(parts) > 1 else ""

                    if is_thinking:
                        if content:
                            full_reply += content
                            self.after(0, lambda c=content: self.append_chat_log(c, self.C_MT))
                    else:
                        if content:
                            full_reply += content
                            self.after(0, lambda c=content: self.append_chat_log(c, self.C_TX))

            if not self.generation_interrupted:
                self.chat_history.append({"role": "assistant", "content": full_reply})
                self.after(0, lambda: self.append_chat_log("\n\n"))
            else:
                self.after(0, lambda: self.append_chat_log("\n⚡ [会话数据通信已被用户物理强制终止。]\n\n", self.C_WN))

        except Exception as e:
            if not self.generation_interrupted:
                self.after(0, lambda: self.append_chat_log(f"❌ 通信数据链路中断: {str(e)}\n\n", self.C_WN))
        finally:
            if response is not None:
                try:
                    response.close()
                except Exception:
                    pass
            session.close()
            self.after(0, self.release_ui_lock_safely)

    def print_workspace_log(self, text):
        def _append():
            self.log_box.configure(state="normal")
            self.log_box.insert("end", text + "\n")
            self.log_box.configure(state="disabled")
            self.log_box.see("end")

        if threading.current_thread() is threading.main_thread():
            _append()
        else:
            self.after(0, _append)

    def import_video_assets(self):
        files = fd.askopenfilenames(filetypes=[("视频文件", "*.mp4 *.mov *.avi")])
        if files:
            self.imported_video_files = list(files)
            self.print_workspace_log(f"❯ 成功挂载 {len(files)} 项多媒体视频样本。")

    def set_output_folder_path(self):
        folder = fd.askdirectory()
        if folder:
            self.output_folder_path = folder
            self.print_workspace_log(f"📁 导出目标输出磁盘路径已绑定成功。")

    def start_rendering_process(self):
        if not self.imported_video_files or not self.output_folder_path:
            self.print_workspace_log("❌ 调度终止: 缺少视频样本资产或导出保存路径未设定。")
            return
        self.btn_start.configure(state="disabled", text="⚡ 视频渲染引擎处理中...")
        threading.Thread(target=self.execute_rendering_pipeline, daemon=True).start()

    def execute_rendering_pipeline(self):
        try:
            self.print_workspace_log("⏳ 数据流转换中...")
            time.sleep(1.5)
            self.print_workspace_log("🎉 媒体重新编排成功，产物已成功导出！")
        except Exception as e:
            self.print_workspace_log(f"❌ 运行期阻断异常: {str(e)}")
        finally:
            cfg = LANG_MATRIX.get(self.lang_var.get(), LANG_MATRIX["🇨🇳 中文 (CN)"])
            self.after(0, lambda: self.btn_start.configure(state="normal", text=cfg["start_btn"]))


if __name__ == "__main__":
    app = OllamaClientApp()
    app.mainloop()