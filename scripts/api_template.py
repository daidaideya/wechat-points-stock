# -*- coding: utf-8 -*-
"""
积分上报 API 调用模板 (Python)

此模板用于将脚本运行产生的积分数据上报到监控系统。
你可以直接复制此类到你的脚本中使用。
"""

import requests
import json
import time
import os

class PointsReporter:
    def __init__(self, api_url=None, api_token=None):
        """
        初始化上报器
        :param api_url: 监控系统地址 (例如 http://192.168.1.100:5711)
        :param api_token: API 认证 Token
        """
        # 默认配置，建议根据实际情况修改
        self.api_url = api_url or "http://127.0.0.1:5711"
        self.api_token = api_token or "YOUR_TOKEN_HERE"
        
        # 也可以尝试从环境变量读取
        if not api_url:
            self.api_url = os.getenv("POINTS_MONITOR_URL", self.api_url)
        if not api_token:
            self.api_token = os.getenv("POINTS_MONITOR_TOKEN", self.api_token)

    def report(self, script_name, wechat_id, points_data):
        """
        上报积分数据
        :param script_name: 脚本名称/ID (如 "jd_bean_sign")
        :param wechat_id: 当前执行的微信号 (如 "wxid_xxxx")
        :param points_data: 积分列表，格式如下:
               [
                   {
                       "program_id": "小程序唯一ID",
                       "program_name": "小程序名称",
                       "current_points": 100
                   },
                   ...
               ]
        """
        url = f"{self.api_url.rstrip('/')}/api/v1/qinglong/report"
        
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
        
        # 构造符合 API 要求的请求体
        payload = {
            "script_id": script_name,
            "execution_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "data": {
                "wechat_accounts": [
                    {
                        "wechat_id": wechat_id,
                        # "nickname": "可选昵称", # 如果脚本能获取到昵称也可以传
                        "points_data": points_data
                    }
                ]
            }
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            if response.status_code == 200:
                print(f"✅ [积分监控] 上报成功: {len(points_data)} 条数据")
                return True
            else:
                print(f"❌ [积分监控] 上报失败: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ [积分监控] 网络错误: {e}")
            return False

# ================= 使用示例 =================

if __name__ == "__main__":
    # 1. 配置
    # 优先使用环境变量，否则使用默认值
    MONITOR_URL = os.getenv("POINTS_MONITOR_URL")
    MONITOR_TOKEN = os.getenv("POINTS_MONITOR_TOKEN")
    
    print(f"Using Monitor URL: {MONITOR_URL}")
    
    # 2. 初始化
    reporter = PointsReporter(MONITOR_URL, MONITOR_TOKEN)
    
    # 3. 准备数据 (在你的脚本逻辑中收集这些数据)
    current_wechat_id = "wxid_example_user"
    
    my_points = [
        {
            "program_id": "mp_signin_daily",
            "program_name": "每日签到",
            "current_points": 520
        },
        {
            "program_id": "mp_fruit_farm",
            "program_name": "水果农场",
            "current_points": 1024
        }
    ]
    
    # 4. 上报
    reporter.report(
        script_name="test_script_v1", 
        wechat_id=current_wechat_id, 
        points_data=my_points
    )
