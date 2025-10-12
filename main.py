import tkinter as tk
from tkinter import simpledialog, messagebox
from time import strftime, localtime
import time
import threading
import winsound

class DesktopClock:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("桌面时钟")
        
        # 设置窗口属性
        self.is_topmost = True  # 添加置顶状态标志
        self.root.attributes('-topmost', self.is_topmost)  # 窗口置顶
        self.root.attributes('-alpha', 0.8)     # 设置透明度
        self.root.overrideredirect(True)        # 无边框窗口
        
        # 用于存储计时器和闹钟线程
        self.timer_thread = None
        self.alarm_thread = None
        self.is_timer_running = False
        self.is_alarm_running = False
        
        # 创建标签显示时间
        self.label = tk.Label(
            self.root,
            font=('Arial', 40),
            background='black',
            foreground='white',
            padx=20,
            pady=10
        )
        self.label.pack()
        
        # 创建控制按钮区域
        self.create_control_buttons()
        
        # 绑定鼠标事件用于拖动窗口
        self.label.bind('<Button-1>', self.start_move)
        self.label.bind('<B1-Motion>', self.on_move)
        
        # 绑定右键菜单
        self.label.bind('<Button-3>', self.show_menu)
        
        # 创建右键菜单
        self.menu = tk.Menu(self.root, tearoff=0)
        self.topmost_var = tk.BooleanVar(value=self.is_topmost)
        self.menu.add_checkbutton(label="置顶显示", variable=self.topmost_var, command=self.toggle_topmost)
        self.menu.add_separator()
        self.menu.add_command(label="设置计时器", command=self.show_timer_dialog)
        self.menu.add_command(label="设置闹钟", command=self.show_alarm_dialog)
        self.menu.add_separator()
        self.menu.add_command(label="退出", command=self.root.quit)
        
        # 初始化计时器和闹钟
        self.timer_remaining = 0
        self.alarm_time = None
        
        # 更新时间的函数
        self.update_time()
        
        # 设置窗口位置和大小
        self.set_window_position()
        
        # 添加全局快捷键
        self.root.bind('<Control-Alt-T>', lambda e: self.toggle_topmost())
        
    def toggle_topmost(self):
        self.is_topmost = self.topmost_var.get()
        self.root.attributes('-topmost', self.is_topmost)
        # 如果取消置顶，临时置顶以显示菜单
        if not self.is_topmost:
            self.root.attributes('-topmost', True)
            self.root.after(100, lambda: self.root.attributes('-topmost', False))
        
    def create_control_buttons(self):
        """创建计时器和闹钟控制按钮"""
        # 创建按钮框架
        button_frame = tk.Frame(self.root, bg='black')
        button_frame.pack(pady=5)
        
        # 计时器按钮
        self.timer_button = tk.Button(
            button_frame,
            text="计时器",
            font=('Arial', 10),
            bg='#333333',
            fg='white',
            width=8,
            command=self.show_timer_dialog
        )
        self.timer_button.pack(side=tk.LEFT, padx=5)
        
        # 闹钟按钮
        self.alarm_button = tk.Button(
            button_frame,
            text="闹钟",
            font=('Arial', 10),
            bg='#333333',
            fg='white',
            width=8,
            command=self.show_alarm_dialog
        )
        self.alarm_button.pack(side=tk.LEFT, padx=5)
        
    def show_timer_dialog(self):
        """显示计时器设置对话框"""
        try:
            minutes = simpledialog.askinteger(
                "设置计时器",
                "请输入分钟数:",
                minvalue=1,
                maxvalue=180
            )
            if minutes:
                self.start_timer(minutes * 60)
        except Exception as e:
            messagebox.showerror("错误", f"设置计时器时出错: {e}")
    
    def show_alarm_dialog(self):
        """显示闹钟设置对话框"""
        try:
            time_str = simpledialog.askstring(
                "设置闹钟",
                "请输入时间 (HH:MM):"
            )
            if time_str:
                # 验证时间格式
                try:
                    hour, minute = map(int, time_str.split(':'))
                    if 0 <= hour <= 23 and 0 <= minute <= 59:
                        self.set_alarm(hour, minute)
                except:
                    messagebox.showerror("错误", "时间格式不正确，请使用 HH:MM 格式")
        except Exception as e:
            messagebox.showerror("错误", f"设置闹钟时出错: {e}")
    
    def set_alarm(self, hour, minute):
        """设置闹钟"""
        self.alarm_time = (hour, minute)
        # 检查是否已经启动闹钟线程
        if not self.is_alarm_running:
            self.is_alarm_running = True
            self.alarm_thread = threading.Thread(target=self._monitor_alarm, daemon=True)
            self.alarm_thread.start()
            messagebox.showinfo("闹钟设置", f"闹钟已设置为 {hour:02d}:{minute:02d}\n将在到达时间前5秒开始倒计时提示。")
    
    def start_timer(self, duration):
        """启动计时器"""
        self.timer_remaining = duration
        self.is_timer_running = True
        # 启动计时器线程
        self.timer_thread = threading.Thread(target=self._run_timer, daemon=True)
        self.timer_thread.start()
        messagebox.showinfo("计时器开始", f"计时器已启动: {duration} 秒")
    
    def _run_timer(self):
        """计时器线程主循环"""
        while self.timer_remaining > 0 and self.is_timer_running:
            time.sleep(1)
            self.timer_remaining -= 1
            # 在计时器结束时显示弹窗
            if self.timer_remaining == 0:
                self.root.after(0, self._timer_completed)
    
    def _monitor_alarm(self):
        """闹钟监控线程"""
        while self.is_alarm_running and self.alarm_time:
            current_time = localtime()
            current_hour = current_time.tm_hour
            current_minute = current_time.tm_min
            current_second = current_time.tm_sec
            
            target_hour, target_minute = self.alarm_time
            
            # 检查是否到达闹钟时间前5秒
            if (current_hour == target_hour and 
                current_minute == target_minute and 
                current_second >= 55):
                self.root.after(0, self._alarm_countdown_start)
                break
            
            # 检查是否精确到达目标时间
            if (current_hour == target_hour and 
                current_minute == target_minute):
                self.root.after(0, self._alarm_triggered)
                break
            
            time.sleep(1)
        
        self.is_alarm_running = False
    
    def _timer_completed(self):
        """计时器完成时的处理"""
        self.is_timer_running = False
        # 播放提示音
        try:
            winsound.PlaySound("SystemExclamation", winsound.SND_ALIAS)
        except:
            pass
        
        messagebox.showinfo("计时器", "计时器结束！")
    
    def _show_countdown_popup(self, seconds_left):
        """显示倒计时弹窗（计时器专用）"""
        popup = tk.Toplevel(self.root)
        popup.title("计时器倒计时")
        popup.geometry("300x150")
        popup.attributes('-topmost', True)
        
        countdown_label = tk.Label(
            popup,
            text=f"倒计时: {seconds_left} 秒",
            font=('Arial', 20),
            bg='red',
            fg='white'
        )
        countdown_label.pack(expand=True, fill='both')
        
        def update_countdown():
            nonlocal seconds_left
            if seconds_left > 0:
                countdown_label.config(text=f"倒计时: {seconds_left} 秒")
            seconds_left -= 1
            if seconds_left >= 0:
                popup.after(1000, update_countdown)
            else:
                popup.destroy()
        
        update_countdown()
    
    def _alarm_countdown_start(self):
        """闹钟倒计时开始（前5秒）"""
        popup = tk.Toplevel(self.root)
        popup.title("闹钟倒计时")
        popup.geometry("300x150")
        popup.attributes('-topmost', True)
        
        # 创建倒计时标签
        countdown_label = tk.Label(
            popup,
            text="闹钟即将响起！\n倒计时: 5 秒",
            font=('Arial', 16),
            bg='orange',
            fg='white'
        )
        countdown_label.pack(expand=True, fill='both')
        
        self._alarm_countdown(popup, countdown_label, 5)
    
    def _alarm_countdown(self, popup, label, seconds_left):
        """闹钟倒计时更新"""
        if seconds_left > 0:
            label.config(text=f"闹钟即将响起！\n倒计时: {seconds_left} 秒")
            seconds_left -= 1
            if seconds_left >= 0:
                popup.after(1000, self._alarm_countdown, popup, label, seconds_left)
        else:
            popup.destroy()
            self._alarm_triggered()
    
    def _alarm_triggered(self):
        """闹钟触发处理"""
        self.is_alarm_running = False
        try:
            # 播放闹钟铃声
            winsound.PlaySound("SystemExclamation", winsound.SND_ALIAS)
        except:
            pass
        
        messagebox.showinfo("闹钟", "闹钟时间到！")
    
    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def on_move(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.root.winfo_x() + deltax
        y = self.root.winfo_y() + deltay
        self.root.geometry(f"+{x}+{y}")
    
    def show_menu(self, event):
        # 显示菜单时临时置顶
        self.root.attributes('-topmost', True)
        self.menu.post(event.x_root, event.y_root)
        # 根据当前设置恢复置顶状态
        self.root.after(100, lambda: self.root.attributes('-topmost', self.is_topmost))
    
    def set_window_position(self):
        # 获取屏幕尺寸
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # 设置窗口位置在屏幕右上角
        window_width = 200
        window_height = 120
        x = screen_width - window_width - 20
        y = 20
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
    
    def update_time(self):
        # 更新时间显示
        current_time = strftime("%H:%M:%S")
        self.label.config(text=current_time)
        # 每秒更新一次
        self.root.after(1000, self.update_time)
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    clock = DesktopClock()
    clock.run()