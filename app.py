#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Flask, jsonify
from flask_cors import CORS
import json
import os
import threading
import time
from datetime import datetime, timedelta
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# 全局变量存储新闻数据
news_data = {}
last_update = None
update_lock = threading.Lock()

def load_news_data():
    """从文件加载新闻数据"""
    global news_data, last_update
    
    try:
        # 优先加载测试结果
        if os.path.exists('/workspace/test_results.json'):
            with open('/workspace/test_results.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
            with update_lock:
                news_data = data
                last_update = datetime.now()
            logger.info("测试新闻数据加载成功")
        elif os.path.exists('/workspace/news_data.json'):
            with open('/workspace/news_data.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
            with update_lock:
                news_data = data
                last_update = datetime.now()
            logger.info("新闻数据加载成功")
        else:
            logger.warning("没有找到新闻数据文件")
            
    except Exception as e:
        logger.error(f"加载新闻数据失败: {e}")

def update_news_data():
    """更新新闻数据（后台任务）"""
    global news_data, last_update
    
    logger.info("开始后台更新新闻数据")
    
    try:
        # 动态导入scraper模块避免启动时阻塞
        from scraper import NewsScraper
        scraper = NewsScraper()
        new_data = scraper.scrape_all_news()
        
        if new_data:
            # 保存到文件
            with open('/workspace/news_data.json', 'w', encoding='utf-8') as f:
                json.dump(new_data, f, ensure_ascii=False, indent=2)
            
            with update_lock:
                news_data = new_data
                last_update = datetime.now()
            
            logger.info(f"新闻数据更新成功，共 {new_data.get('total_items', 0)} 条新闻")
        else:
            logger.error("抓取到的新闻数据为空")
            
    except Exception as e:
        logger.error(f"更新新闻数据失败: {e}")

def schedule_updates():
    """设置定时更新任务"""
    import schedule
    # 每小时更新一次
    schedule.every().hour.do(update_news_data)
    
    while True:
        schedule.run_pending()
        time.sleep(60)  # 每分钟检查一次

@app.route('/')
def index():
    """主页"""
    try:
        with open('/workspace/index.html', 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.error(f"读取index.html失败: {e}")
        return "页面加载失败", 500

@app.route('/api/news')
def get_news():
    """获取新闻数据API"""
    try:
        with update_lock:
            if not news_data:
                return jsonify({"error": "暂无新闻数据，请稍后再试"}), 503
            
            # 返回新闻数据，排除时间戳等元数据
            response_data = {}
            categories = ['mobile', 'smart_home', 'automotive', 'chip', 'os']
            
            for category in categories:
                response_data[category] = news_data.get(category, [])
            
            response_data['last_update'] = last_update.isoformat() if last_update else None
            response_data['total_items'] = news_data.get('total_items', 0)
            
            return jsonify(response_data)
            
    except Exception as e:
        logger.error(f"获取新闻数据失败: {e}")
        return jsonify({"error": "获取新闻数据失败"}), 500

@app.route('/api/update')
def manual_update():
    """手动更新新闻数据"""
    try:
        # 在后台线程中更新，避免阻塞请求
        threading.Thread(target=update_news_data, daemon=True).start()
        return jsonify({"message": "更新任务已启动"})
    except Exception as e:
        logger.error(f"手动更新失败: {e}")
        return jsonify({"error": "更新失败"}), 500

@app.route('/api/status')
def get_status():
    """获取系统状态"""
    try:
        with update_lock:
            status = {
                "last_update": last_update.isoformat() if last_update else None,
                "total_items": news_data.get('total_items', 0),
                "categories": {}
            }
            
            categories = ['mobile', 'smart_home', 'automotive', 'chip', 'os']
            for category in categories:
                status["categories"][category] = len(news_data.get(category, []))
            
            return jsonify(status)
            
    except Exception as e:
        logger.error(f"获取状态失败: {e}")
        return jsonify({"error": "获取状态失败"}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "页面不存在"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "服务器内部错误"}), 500

def initialize_app():
    """初始化应用"""
    logger.info("正在初始化应用...")
    
    # 加载现有数据
    load_news_data()
    
    # 延迟启动后台任务，避免阻塞服务器启动
    def delayed_start():
        time.sleep(10)  # 等待10秒让服务器完全启动
        logger.info("启动后台数据更新任务...")
        threading.Thread(target=update_news_data, daemon=True).start()
        
        logger.info("启动定时更新任务...")
        threading.Thread(target=schedule_updates, daemon=True).start()
    
    threading.Thread(target=delayed_start, daemon=True).start()
    logger.info("应用初始化完成")

if __name__ == '__main__':
    # 初始化应用
    initialize_app()
    
    # 启动Flask应用
    logger.info("启动Web服务器...")
    app.run(host='0.0.0.0', port=5000, debug=True)