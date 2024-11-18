import tkinter as tk
from tkinter import messagebox, simpledialog, Toplevel, Menu
import json
import os
import threading
import time
from datetime import datetime, timedelta
from login_cookie import LoginManager, Logger  # 导入您已有的登录管理和日志类
from qiandao import submit_clockin  # 导入签到功能


class AccountManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("XXT定时签到系统")
        self.root.geometry("600x500")  # 设置固定窗口大小
        self.root.resizable(False, False)  # 禁止拉大或缩小窗口
        # 使窗口居中
        self.center_window(root)
        self.logger = Logger()

        self.current_account = None  # 初始化当前账号属性

        # 初始化Tkinter界面布局
        self.setup_ui()

        # 启动签到检查线程
        self.check_thread = threading.Thread(
            target=self.check_signin_time_thread, daemon=True)
        self.check_thread.start()

    def setup_ui(self):
        # 左侧账号列表栏
        self.account_frame = tk.LabelFrame(
            self.root, text="账号列表", padx=5, pady=5)
        self.account_frame.grid(
            row=0, column=0, rowspan=5, padx=5, pady=5, sticky="ns")

        self.account_list = tk.Listbox(self.account_frame, height=15)
        self.account_list.pack(fill=tk.BOTH, expand=True)
        self.account_list.bind("<Button-3>", self.show_account_menu)  # 右键菜单
        self.account_list.bind("<<ListboxSelect>>",
                               self.load_account_config)  # 选中账号加载配置

        # 右侧配置栏
        self.config_frame = tk.LabelFrame(
            self.root, text="配置参数", padx=5, pady=5)
        self.config_frame.grid(row=0, column=1, padx=5, pady=5)

        self.address_entry = tk.Entry(self.config_frame)
        self.geo_entry = tk.Entry(self.config_frame)
        self.sign_in_time_entry = tk.Entry(self.config_frame)  # 定时签到时间输入框

        # 在签到时间输入框中添加提示
        self.sign_in_time_entry.insert(0, "HH:MM:SS")  # 插入提示文本

        # 绑定事件以清除提示文本
        self.sign_in_time_entry.bind("<FocusIn>", self.clear_placeholder)
        self.sign_in_time_entry.bind("<FocusOut>", self.set_placeholder)

        # 标签与输入框
        labels = ["签到地址：", "地理坐标：", "签到时间："]
        entries = [self.address_entry, self.geo_entry, self.sign_in_time_entry]
        for i, (label_text, entry) in enumerate(zip(labels, entries)):
            tk.Label(self.config_frame, text=label_text).grid(
                row=i, column=0, padx=5, pady=2, sticky="e")
            entry.grid(row=i, column=1, padx=5, pady=2)

        # 保存配置按钮
        self.save_config_button = tk.Button(
            self.config_frame, text="保存配置", command=self.save_account_config)
        self.save_config_button.grid(row=3, column=0, columnspan=2, pady=5)

        # 底部日志栏
        self.log_frame = tk.LabelFrame(self.root, text="日志", padx=5, pady=5)
        self.log_frame.grid(row=5, column=0, columnspan=2, padx=5, pady=5)

        self.log_text = tk.Text(self.log_frame, height=10, state="disabled")
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # 加载本地账号列表
        self.load_accounts()

    def clear_placeholder(self, event):
        """清除输入框中的提示文本"""
        if self.sign_in_time_entry.get() == "HH:MM:SS":
            self.sign_in_time_entry.delete(0, tk.END)

    def set_placeholder(self, event):
        """如果输入框为空，则重新设置提示文本"""
        if self.sign_in_time_entry.get() == "":
            self.sign_in_time_entry.insert(0, "HH:MM:SS")

    def show_account_menu(self, event):
        # 右键菜单，选择添加或删除账号
        menu = Menu(self.root, tearoff=0)
        menu.add_command(label="添加账号", command=self.add_account)
        menu.add_command(label="删除账号", command=self.delete_account)
        menu.post(event.x_root, event.y_root)

    def add_account(self):
        # 添加账号窗口
        add_window = Toplevel(self.root)
        add_window.title("添加账号")
        add_window.geometry("220x110")  # 设置固定窗口大小
        add_window.resizable(False, False)  # 禁止拉大或缩小窗口

        # 使窗口居中
        self.center_window(add_window)

        tk.Label(add_window, text="账号：").grid(row=0, column=0, padx=5, pady=5)
        tk.Label(add_window, text="密码：").grid(row=1, column=0, padx=5, pady=5)

        username_entry = tk.Entry(add_window)
        password_entry = tk.Entry(add_window, show="*")
        username_entry.grid(row=0, column=1, padx=5, pady=5)
        password_entry.grid(row=1, column=1, padx=5, pady=5)

        def login_account():
            username = username_entry.get().strip()
            password = password_entry.get().strip()
            if not username or not password:
                messagebox.showwarning("警告", "请输入账号和密码")
                return

            login_manager = LoginManager(self.logger)
            res = login_manager.login(username, password)
            if res.get("status"):
                self.log_message(f"账号 {username} 登录成功")
                self.load_accounts()  # 刷新账号列表
                add_window.destroy()
            else:
                self.log_message(
                    f"账号 {username} 登录失败: {res.get('mes', '未知错误')}")

        login_button = tk.Button(add_window, text="登录", command=login_account)
        login_button.grid(row=2, column=0, columnspan=2, pady=10)

    def center_window(self, window):
        """将窗口显示在屏幕中央"""
        window.update_idletasks()
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        size = tuple(int(i)
                     for i in window.geometry().split("+")[0].split("x"))
        x = screen_width / 2 - size[0] / 2
        y = screen_height / 2 - size[1] / 2
        window.geometry("%dx%d+%d+%d" % (size[0], size[1], x, y))

    def delete_account(self):
        # 删除选中的账号
        selected_account = self.account_list.get(tk.ACTIVE)
        if selected_account:
            account_path = os.path.join('./data', selected_account)
            for file in os.listdir(account_path):
                os.remove(os.path.join(account_path, file))
            os.rmdir(account_path)
            self.load_accounts()
            self.log_message(f"账号 {selected_account} 已删除")

    def log_message(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"{timestamp} - {message}"
        self.log_text.config(state="normal")
        self.log_text.insert("end", log_message + "\n")
        self.log_text.config(state="disabled")
        self.log_text.see("end")
        self.logger.log(message)

    def load_accounts(self):
        # 加载本地账号
        self.account_list.delete(0, "end")
        for account in os.listdir('./data'):
            if os.path.isdir(os.path.join('./data', account)):
                self.account_list.insert("end", account)

    def load_account_config(self, event=None):
        # 获取 Listbox 当前选中的账号
        selected_index = self.account_list.curselection()
        if not selected_index:
            return

        selected_account = self.account_list.get(selected_index[0])
        self.current_account = selected_account  # 存储当前选中账号名称

        # 加载配置文件
        account_path = os.path.join('./data', selected_account)
        config_file = os.path.join(account_path, 'config.json')
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)

            # 更新 UI 中的输入框内容
            self.address_entry.delete(0, tk.END)
            self.address_entry.insert(0, config.get("address", ""))
            self.geo_entry.delete(0, tk.END)
            self.geo_entry.insert(0, config.get("geolocation", ""))
            self.sign_in_time_entry.delete(0, tk.END)
            self.sign_in_time_entry.insert(0, config.get("sign_in_time", ""))

            # 记录日志
            self.log_message(f"加载了账号 {selected_account} 的配置信息")

    def login_account(self):
        # 登录功能
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        if not username or not password:
            messagebox.showwarning("警告", "请输入账号和密码")
            return

        login_manager = LoginManager(self.logger)
        res = login_manager.login(username, password)
        if res.get("status"):
            self.log_message(f"账号 {username} 登录成功")
            self.load_accounts()
        else:
            self.log_message(f"账号 {username} 登录失败: {res.get('mes', '未知错误')}")

    def save_account_config(self):
        # 保存账号的签到配置信息
        if self.current_account is None:
            messagebox.showwarning("警告", "请选择一个账号进行配置")
            return

        username = self.current_account
        address = self.address_entry.get().strip()
        geolocation = self.geo_entry.get().strip()
        sign_in_time = self.sign_in_time_entry.get().strip()

        # 创建账号文件夹并保存配置
        account_path = os.path.join('./data', username)
        os.makedirs(account_path, exist_ok=True)
        config_file = os.path.join(account_path, 'config.json')

        # 读取现有配置并更新（不覆盖密码字段）
        config = {}
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)

        # 只更新相关的签到配置
        config["address"] = address
        config["geolocation"] = geolocation
        config["sign_in_time"] = sign_in_time

        # 保存更新后的配置
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=4)

        self.log_message(f"账号 {username} 的配置已保存")

    def signin(self, username=None):
        selected_account = username or self.current_account
        if not selected_account:
            self.root.after(
                0, lambda: messagebox.showwarning("警告", "请选择一个账号进行签到"))
            return

        # 读取账号的签到配置信息
        account_path = os.path.join('./data', selected_account)
        config_file = os.path.join(account_path, 'config.json')
        if not os.path.exists(config_file):
            self.root.after(
                0, lambda: messagebox.showwarning("警告", "该账号缺少配置文件"))
            return

        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)

        address = config.get("address")
        geolocation = config.get("geolocation")
        sign_in_time = config.get("sign_in_time")
        password = config.get("password")  # 读取密码
        pcid = config.get("PCID")
        pcmajorid = config.get("PCMAJORID")
        recruitid = config.get("RecruitID")

        # 固定签到时间段
        work_start = "08:00:00"
        work_end = "17:00:00"

        # 加载和检查cookies
        login_manager = LoginManager(
            self.logger, cookie_file=os.path.join(account_path, 'cookies.json'))

        # 检查cookie是否过期
        if login_manager.is_cookies_expired():
            # 如果过期，重新登录并保存cookie
            if login_manager.login(selected_account, password):
                self.log_message(f"账号 {selected_account} 重新登录成功")
            else:
                self.root.after(0, lambda: messagebox.showwarning(
                    "警告", "登录失败，请检查账号和密码"))
                return

        # 执行签到请求，传递日志更新回调
        result = submit_clockin(
            session=login_manager.session,
            address=address,
            geolocation=geolocation,
            pcid=pcid,
            pcmajorid=pcmajorid,
            recruitid=recruitid,
            workStart=work_start,
            workEnd=work_end,
            log_message_callback=lambda msg: self.log_message(msg)  # 传递日志回调
        )

        # 使用after在主线程中更新日志
        self.root.after(0, lambda: self.log_message(
            f"账号 {selected_account} 签到请求已发送，结果: {result}"))

    def check_signin_time_thread(self):
        # 后台线程定时检查是否需要签到
        while True:
            for account in os.listdir('./data'):
                account_path = os.path.join('./data', account)
                config_file = os.path.join(account_path, 'config.json')
                if not os.path.exists(config_file):
                    continue

                # 读取账号的定时签到配置
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                sign_in_time_str = config.get("sign_in_time")
                if not sign_in_time_str:
                    continue

                # 当前时间与签到时间对比
                sign_in_time = datetime.strptime(
                    sign_in_time_str, "%H:%M:%S").time()
                now = datetime.now().time()
                if now >= sign_in_time and (datetime.combine(datetime.today(), now) - datetime.combine(datetime.today(), sign_in_time)) < timedelta(minutes=1):
                    self.signin(username=account)

            # 每分钟检查一次
            time.sleep(60)


# 主程序入口
if __name__ == "__main__":
    root = tk.Tk()
    app = AccountManagerApp(root)
    root.mainloop()
