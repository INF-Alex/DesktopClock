import tkinter as tk
from tkinter import simpledialog, messagebox, ttk
from time import strftime, localtime
import time
import threading
import winsound
from datetime import datetime, timedelta
import calendar

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
        
        # 存储闹钟和计时器列表
        self.alarms = []  # 格式: {'time': (h,m,s), 'repeat': 'daily/weekly/specific', 'day': None, 'date': None, 'active': True}
        self.timers = []  # 格式: {'duration': seconds, 'start_time': timestamp, 'active': True}
        
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
        self.menu.add_command(label="查看闹钟和计时器", command=self.show_alarms_timers)
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
        
        # 启动闹钟监控线程
        self.start_alarm_monitor()

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
            width=10,
            command=self.show_timer_dialog
        )
        self.timer_button.pack(side=tk.LEFT, padx=2)
        
        # 闹钟按钮
        self.alarm_button = tk.Button(
            button_frame,
            text="闹钟",
            font=('Arial', 10),
            bg='#333333',
            fg='white',
            width=10,
            command=self.show_alarm_dialog
        )
        self.alarm_button.pack(side=tk.LEFT, padx=2)
        
        # 查看按钮
        self.view_button = tk.Button(
            button_frame,
            text="查看",
            font=('Arial', 10),
            bg='#333333',
            fg='white',
            width=10,
            command=self.show_alarms_timers
        )
        self.view_button.pack(side=tk.LEFT, padx=2)

    def show_timer_dialog(self):
        """显示计时器设置对话框"""
        dialog = tk.Toplevel(self.root)
        dialog.title("设置计时器")
        dialog.geometry("400x300")
        dialog.attributes('-topmost', True)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # 创建输入框架
        input_frame = tk.Frame(dialog, padx=20, pady=20)
        input_frame.pack(fill='both', expand=True)
        
        tk.Label(input_frame, text="设置计时器（精确到秒）", font=('Arial', 14)).pack(pady=10)
        
        # 时间输入框架
        time_frame = tk.Frame(input_frame)
        time_frame.pack(pady=10)
        
        tk.Label(time_frame, text="小时:").grid(row=0, column=0, padx=5)
        hour_var = tk.StringVar(value="0")
        hour_spinbox = tk.Spinbox(time_frame, from_=0, to=23, width=5, textvariable=hour_var)
        hour_spinbox.grid(row=0, column=1, padx=5)
        
        tk.Label(time_frame, text="分钟:").grid(row=0, column=2, padx=5)
        minute_var = tk.StringVar(value="0")
        minute_spinbox = tk.Spinbox(time_frame, from_=0, to=59, width=5, textvariable=minute_var)
        minute_spinbox.grid(row=0, column=3, padx=5)
        
        tk.Label(time_frame, text="秒:").grid(row=0, column=4, padx=5)
        second_var = tk.StringVar(value="0")
        second_spinbox = tk.Spinbox(time_frame, from_=0, to=59, width=5, textvariable=second_var)
        second_spinbox.grid(row=0, column=5, padx=5)
        
        def start_timer():
            try:
                hours = int(hour_var.get())
                minutes = int(minute_var.get())
                seconds = int(second_var.get())
                
                total_seconds = hours * 3600 + minutes * 60 + seconds
                
                if total_seconds <= 0:
                    messagebox.showerror("错误", "计时器时间必须大于0秒")
                    return
                
                # 添加到计时器列表
                timer_data = {
                    'duration': total_seconds,
                    'start_time': time.time(),
                    'active': True
                }
                self.timers.append(timer_data)
                
                # 启动计时器线程
                if not self.is_timer_running:
                    self.is_timer_running = True
                    self.timer_thread = threading.Thread(target=self._monitor_timers, daemon=True)
                    self.timer_thread.start()
                
                dialog.destroy()
                messagebox.showinfo("计时器开始", f"计时器已启动: {hours:02d}:{minutes:02d}:{seconds:02d}")
                
            except ValueError:
                messagebox.showerror("错误", "请输入有效的数字")
        
        def cancel():
            dialog.destroy()
        
        # 按钮框架
        button_frame = tk.Frame(input_frame)
        button_frame.pack(pady=20)
        
        tk.Button(button_frame, text="开始", command=start_timer, width=10).pack(side=tk.LEFT, padx=10)
        tk.Button(button_frame, text="取消", command=cancel, width=10).pack(side=tk.LEFT, padx=10)

    def show_alarm_dialog(self):
        """显示闹钟设置对话框"""
        dialog = tk.Toplevel(self.root)
        dialog.title("设置闹钟")
        dialog.geometry("500x400")
        dialog.attributes('-topmost', True)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # 创建输入框架
        input_frame = tk.Frame(dialog, padx=20, pady=20)
        input_frame.pack(fill='both', expand=True)
        
        tk.Label(input_frame, text="设置闹钟（精确到秒）", font=('Arial', 14)).pack(pady=10)
        
        # 时间输入框架
        time_frame = tk.Frame(input_frame)
        time_frame.pack(pady=10)
        
        tk.Label(time_frame, text="小时:").grid(row=0, column=0, padx=5)
        hour_var = tk.StringVar(value="12")
        hour_spinbox = tk.Spinbox(time_frame, from_=0, to=23, width=5, textvariable=hour_var)
        hour_spinbox.grid(row=0, column=1, padx=5)
        
        tk.Label(time_frame, text="分钟:").grid(row=0, column=2, padx=5)
        minute_var = tk.StringVar(value="0")
        minute_spinbox = tk.Spinbox(time_frame, from_=0, to=59, width=5, textvariable=minute_var)
        minute_spinbox.grid(row=0, column=3, padx=5)
        
        tk.Label(time_frame, text="秒:").grid(row=0, column=4, padx=5)
        second_var = tk.StringVar(value="0")
        second_spinbox = tk.Spinbox(time_frame, from_=0, to=59, width=5, textvariable=second_var)
        second_spinbox.grid(row=0, column=5, padx=5)
        
        # 重复选项框架
        repeat_frame = tk.LabelFrame(input_frame, text="重复选项", padx=10, pady=10)
        repeat_frame.pack(fill='x', pady=10)
        
        repeat_var = tk.StringVar(value="daily")
        
        tk.Radiobutton(repeat_frame, text="每天", variable=repeat_var, value="daily").pack(anchor='w')
        tk.Radiobutton(repeat_frame, text="每周", variable=repeat_var, value="weekly").pack(anchor='w')
        
        # 星期选择（仅当选择每周时显示）
        day_frame = tk.Frame(repeat_frame)
        day_frame.pack(anchor='w', pady=5)
        
        day_var = tk.StringVar(value="0")  # 0=周一, 6=周日
        day_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        day_menu = ttk.Combobox(day_frame, textvariable=day_var, values=day_names, state="readonly", width=8)
        day_menu.set("周一")
        day_menu.pack(side=tk.LEFT, padx=5)
        
        tk.Radiobutton(repeat_frame, text="特定日期", variable=repeat_var, value="specific").pack(anchor='w')
        
        # 日期选择框架（仅当选择特定日期时显示）
        date_frame = tk.Frame(repeat_frame)
        date_frame.pack(anchor='w', pady=5)
        
        # 简单的日期输入
        date_label = tk.Label(date_frame, text="日期 (YYYY-MM-DD):")
        date_label.pack(side=tk.LEFT, padx=5)
        date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        date_entry = tk.Entry(date_frame, textvariable=date_var, width=12)
        date_entry.pack(side=tk.LEFT, padx=5)
        
        def set_alarm():
            try:
                hour = int(hour_var.get())
                minute = int(minute_var.get())
                second = int(second_var.get())
                repeat_type = repeat_var.get()
                
                if not (0 <= hour <= 23 and 0 <= minute <= 59 and 0 <= second <= 59):
                    messagebox.showerror("错误", "时间格式不正确")
                    return
                
                alarm_data = {
                    'time': (hour, minute, second),
                    'repeat': repeat_type,
                    'active': True
                }
                
                if repeat_type == "weekly":
                    day_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
                    selected_day = day_var.get()
                    alarm_data['day'] = day_names.index(selected_day)  # 0-6 对应周一至周日
                elif repeat_type == "specific":
                    try:
                        alarm_date = datetime.strptime(date_var.get(), "%Y-%m-%d")
                        alarm_data['date'] = alarm_date
                    except ValueError:
                        messagebox.showerror("错误", "日期格式不正确，请使用 YYYY-MM-DD 格式")
                        return
                
                self.alarms.append(alarm_data)
                dialog.destroy()
                messagebox.showinfo("闹钟设置", f"闹钟已设置为 {hour:02d}:{minute:02d}:{second:02d}")
                
            except ValueError:
                messagebox.showerror("错误", "请输入有效的数字")
        
        def cancel():
            dialog.destroy()
        
        # 按钮框架
        button_frame = tk.Frame(input_frame)
        button_frame.pack(pady=20)
        
        tk.Button(button_frame, text="设置", command=set_alarm, width=10).pack(side=tk.LEFT, padx=10)
        tk.Button(button_frame, text="取消", command=cancel, width=10).pack(side=tk.LEFT, padx=10)

    def show_alarms_timers(self):
        """显示闹钟和计时器管理界面"""
        dialog = tk.Toplevel(self.root)
        dialog.title("闹钟和计时器管理")
        dialog.geometry("600x400")
        dialog.attributes('-topmost', True)
        dialog.transient(self.root)
        
        # 创建笔记本（选项卡）
        notebook = ttk.Notebook(dialog)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # 闹钟选项卡
        alarm_frame = ttk.Frame(notebook)
        notebook.add(alarm_frame, text="闹钟")
        
        # 闹钟列表
        alarm_listbox = tk.Listbox(alarm_frame, height=10)
        alarm_listbox.pack(fill='both', expand=True, padx=10, pady=10)
        
        # 刷新闹钟列表
        def refresh_alarms():
            alarm_listbox.delete(0, tk.END)
            for i, alarm in enumerate(self.alarms):
                hour, minute, second = alarm['time']
                status = "激活" if alarm['active'] else "禁用"
                time_str = f"{hour}时{minute}分{second}秒"
                if alarm['repeat'] == 'daily':
                    alarm_listbox.insert(tk.END, f"{i+1}. {time_str} - 每天 - {status}")
                elif alarm['repeat'] == 'weekly':
                    days = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
                    day_name = days[alarm.get('day', 0)]
                    alarm_listbox.insert(tk.END, f"{i+1}. {time_str} - 每周{day_name} - {status}")
                else:
                    date_str = alarm.get('date', datetime.now()).strftime("%Y-%m-%d")
                    alarm_listbox.insert(tk.END, f"{i+1}. {time_str} - {date_str} - {status}")
        
        refresh_alarms()
        
        # 闹钟操作按钮
        alarm_button_frame = tk.Frame(alarm_frame)
        alarm_button_frame.pack(fill='x', padx=10, pady=5)
        
        def toggle_alarm():
            selection = alarm_listbox.curselection()
            if selection:
                index = selection[0]
                self.alarms[index]['active'] = not self.alarms[index]['active']
                refresh_alarms()
        
        def delete_alarm():
            selection = alarm_listbox.curselection()
            if selection:
                index = selection[0]
                del self.alarms[index]
                refresh_alarms()
        
        tk.Button(alarm_button_frame, text="切换状态", command=toggle_alarm).pack(side=tk.LEFT, padx=5)
        tk.Button(alarm_button_frame, text="删除", command=delete_alarm).pack(side=tk.LEFT, padx=5)
        
        # 计时器选项卡
        timer_frame = ttk.Frame(notebook)
        notebook.add(timer_frame, text="计时器")
        
        # 计时器列表
        timer_listbox = tk.Listbox(timer_frame, height=10)
        timer_listbox.pack(fill='both', expand=True, padx=10, pady=10)
        
        # 刷新计时器列表
        def refresh_timers():
            # 保存当前选中的项目
            current_selection = timer_listbox.curselection()
            selected_index = current_selection[0] if current_selection else None
            
            timer_listbox.delete(0, tk.END)
            for i, timer in enumerate(self.timers):
                if timer['active']:
                    elapsed = time.time() - timer['start_time']
                    remaining = max(0, timer['duration'] - elapsed)
                    hours = int(remaining // 3600)
                    minutes = int((remaining % 3600) // 60)
                    seconds = int(remaining % 60)
                    timer_listbox.insert(tk.END, f"{i+1}. 剩余: {hours}小时{minutes}分钟{seconds}秒")
                else:
                    timer_listbox.insert(tk.END, f"{i+1}. 已完成")
            
            # 恢复选中的项目
            if selected_index is not None and selected_index < timer_listbox.size():
                timer_listbox.selection_set(selected_index)
        
        # 定期刷新计时器显示
        def update_timer_display():
            refresh_timers()
            dialog.after(1000, update_timer_display)
        
        update_timer_display()
        
        # 计时器操作按钮
        timer_button_frame = tk.Frame(timer_frame)
        timer_button_frame.pack(fill='x', padx=10, pady=5)
        
        def stop_timer():
            selection = timer_listbox.curselection()
            if selection:
                index = selection[0]
                self.timers[index]['active'] = False
                refresh_timers()
        
        def delete_timer():
            selection = timer_listbox.curselection()
            if selection:
                index = selection[0]
                del self.timers[index]
                refresh_timers()
        
        tk.Button(timer_button_frame, text="停止", command=stop_timer).pack(side=tk.LEFT, padx=5)
        tk.Button(timer_button_frame, text="删除", command=delete_timer).pack(side=tk.LEFT, padx=5)
        
        # 关闭按钮
        close_button = tk.Button(dialog, text="关闭", command=dialog.destroy)
        close_button.pack(pady=10)

    def start_alarm_monitor(self):
        """启动闹钟监控线程"""
        if not self.is_alarm_running:
            self.is_alarm_running = True
            self.alarm_thread = threading.Thread(target=self._monitor_alarms, daemon=True)
            self.alarm_thread.start()

    def _monitor_alarms(self):
        """监控所有闹钟"""
        while self.is_alarm_running:
            current_time = localtime()
            current_hour = current_time.tm_hour
            current_minute = current_time.tm_min
            current_second = current_time.tm_sec
            current_weekday = current_time.tm_wday  # 0=周一, 6=周日
            current_date = datetime.now().date()
            
            for alarm in self.alarms:
                if not alarm['active']:
                    continue
                
                alarm_hour, alarm_minute, alarm_second = alarm['time']
                repeat_type = alarm['repeat']
                
                # 检查是否匹配
                match = False
                if repeat_type == 'daily':
                    match = (current_hour == alarm_hour and 
                            current_minute == alarm_minute and 
                            current_second == alarm_second)
                elif repeat_type == 'weekly':
                    match = (current_weekday == alarm.get('day', 0) and
                            current_hour == alarm_hour and 
                            current_minute == alarm_minute and 
                            current_second == alarm_second)
                elif repeat_type == 'specific':
                    alarm_date = alarm.get('date')
                    if alarm_date and alarm_date.date() == current_date:
                        match = (current_hour == alarm_hour and 
                                current_minute == alarm_minute and 
                                current_second == alarm_second)
                
                if match:
                    self.root.after(0, lambda: self._trigger_alarm(alarm))
                    # 避免重复触发
                    time.sleep(1)
            
            time.sleep(0.5)  # 每0.5秒检查一次

    def _monitor_timers(self):
        """监控所有计时器"""
        while self.is_timer_running:
            current_time = time.time()
            active_timers = False
            
            for timer in self.timers:
                if timer['active']:
                    active_timers = True
                    elapsed = current_time - timer['start_time']
                    if elapsed >= timer['duration']:
                        timer['active'] = False
                        self.root.after(0, lambda t=timer: self._timer_completed(t))
            
            # 如果没有活动的计时器，停止监控线程
            if not active_timers:
                self.is_timer_running = False
                break
            
            time.sleep(0.5)  # 每0.5秒检查一次

    def _trigger_alarm(self, alarm):
        """触发闹钟"""
        hour, minute, second = alarm['time']
        try:
            winsound.PlaySound("SystemExclamation", winsound.SND_ALIAS)
        except:
            pass
        
        messagebox.showinfo("闹钟", f"闹钟时间到！\n时间: {hour:02d}:{minute:02d}:{second:02d}")

    def _timer_completed(self, timer):
        """计时器完成"""
        try:
            winsound.PlaySound("SystemExclamation", winsound.SND_ALIAS)
        except:
            pass
        
        messagebox.showinfo("计时器", "计时器结束！")

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
        window_width = 250  # 增加宽度以适应更大的按钮
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