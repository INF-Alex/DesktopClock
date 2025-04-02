import tkinter as tk
from time import strftime
import time

class DesktopClock:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("桌面时钟")
        
        # 设置窗口属性
        self.is_topmost = True  # 添加置顶状态标志
        self.root.attributes('-topmost', self.is_topmost)  # 窗口置顶
        self.root.attributes('-alpha', 0.8)     # 设置透明度
        self.root.overrideredirect(True)        # 无边框窗口
        
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
        self.menu.add_command(label="退出", command=self.root.quit)
        
        # 更新时间的函数
        self.update_time()
        
        # 设置窗口位置
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
        window_height = 100
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