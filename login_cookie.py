import json
import os
import requests
from datetime import datetime, timedelta

class Logger:
    def __init__(self, log_file='log.txt'):
        self.log_file = log_file

    def log(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"{timestamp} - {message}"
        print(log_message)
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_message + "\n")

class LoginManager:
    def __init__(self, logger, cookie_file='cookies.json'):
        self.session = requests.Session()
        self.cookie_file = cookie_file
        self.logger = logger
        self.load_cookies()

    def load_cookies(self):
        if os.path.exists(self.cookie_file):
            with open(self.cookie_file, 'r', encoding='utf-8') as f:
                cookies = json.load(f)
                self.session.cookies.update(requests.utils.cookiejar_from_dict(cookies, overwrite=True))
                self.logger.log("已加载 cookies")

    def save_cookies(self, username):
        dir_path = os.path.join('./data', username)
        os.makedirs(dir_path, exist_ok=True)
        self.cookie_file = os.path.join(dir_path, 'cookies.json')
        with open(self.cookie_file, 'w', encoding='utf-8') as f:
            cookies = requests.utils.dict_from_cookiejar(self.session.cookies)
            json.dump(cookies, f)
            self.logger.log(f"{username} 的 cookies 已保存")

    def login(self, uname, passwd):
        url = "https://passport2-api.chaoxing.com/v11/loginregister"
        data = {
            "code": passwd,
            "cx_xxt_passport": "json",
            "uname": uname,
            "loginType": "1",
            "roleSelect": "true"
        }
        res = self.session.post(url=url, data=data).json()
        if res.get('status'):
            self.save_cookies(uname)
            self.save_account_password(uname, passwd)  # 保存账号和密码
            self.logger.log(f"账号 {uname} 登录成功")
        else:
            self.logger.log(f"账号 {uname} 登录失败: {res.get('mes', '未知错误')}")
        return res

    def save_account_password(self, username, password):
        # 保存账号和密码到config.json
        account_path = os.path.join('./data', username)
        config_file = os.path.join(account_path, 'config.json')
        
        # 读取现有配置并更新
        config = {}
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
        
        config["username"] = username  # 添加或更新用户名
        config["password"] = password    # 添加或更新密码
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=4)


    def is_cookies_expired(self):
        if self.cookie_file and os.path.exists(self.cookie_file):
            with open(self.cookie_file, 'r', encoding='utf-8') as f:
                cookies = json.load(f)
            if "_d" in cookies:
                login_time = datetime.fromtimestamp(int(cookies["_d"]) / 1000)  # 解析时间戳
                return datetime.now() - login_time > timedelta(days=7)
        return True  # 如果没有cookie，视为过期

    def refresh_cookies(self, uname, passwd):
        self.login(uname, passwd)