from datetime import datetime, timedelta

def submit_clockin(session, address, geolocation, workStart, workEnd, log_message_callback):
    # 设置签到的 URL
    base_url = "http://v11194.dgsx.chaoxing.com/mobile/clockin/addclockin2"

    # 定义请求参数
    params = {
        "id": 0,
        "type": 0,
        "recruitId": 1805487,
        "pcid": 14845,
        "pcmajorid": 2504482,
        "address": address,
        "geolocation": geolocation,
        "remark": "",
        "workStart": workStart,
        "workEnd": workEnd,
        "images": "",
        "allowOffset": 2000,
        "offset": 0,
        "offduty": 0,
        "changeLocation": geolocation,
        "statusName": "上班",
        "shouldSignAddress": ""
    }

    # 发送签到请求，附带参数
    response = session.post(base_url, headers={"User-Agent": "Mozilla/5.0"}, params=params)

    if response.status_code == 200:
        print("签到请求成功")
        try:
            response_data = response.json()
            print("响应内容:", response_data)
            # 检查 success 和 msg 字段
            if response_data.get('success') and response_data.get('msg') == '打卡成功':
                log_message_callback("打卡成功")  # 更新日志
                return "打卡成功"
            else:
                log_message_callback(f"签到失败: {response_data.get('msg', '未知错误')}")
                return f"签到失败: {response_data.get('msg', '未知错误')}"
        except ValueError:
            print("响应内容不是 JSON 格式：", response.text)
            log_message_callback("签到请求失败，响应内容不是 JSON 格式")
            return "签到请求失败，响应内容不是 JSON 格式"
    else:
        print("签到请求失败，状态码:", response.status_code)
        log_message_callback(f"签到请求失败，状态码: {response.status_code}")
        return f"签到请求失败，状态码: {response.status_code}"