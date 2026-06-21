#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试脚本 - 验证网页抓取功能
"""

import json
from scraper import NewsScraper
import logging

# 设置日志级别
logging.basicConfig(level=logging.INFO)

def test_single_category(scraper, category):
    """测试单个分类的抓取"""
    print(f"\n=== 测试 {category} 分类 ===")
    
    try:
        items = scraper.scrape_category(category)
        print(f"抓取到 {len(items)} 条新闻")
        
        if items:
            print("\n前3条新闻:")
            for i, item in enumerate(items[:3], 1):
                print(f"{i}. {item['title'][:50]}...")
                print(f"   来源: {item['source']}")
                print(f"   链接: {item['url'][:80]}...")
                if item['summary']:
                    print(f"   摘要: {item['summary'][:100]}...")
                print()
        
        return len(items)
        
    except Exception as e:
        print(f"测试 {category} 分类失败: {e}")
        return 0

def main():
    """主测试函数"""
    print("=== 网页抓取功能测试 ===")
    
    scraper = NewsScraper()
    categories = ['mobile', 'smart_home', 'automotive', 'chip', 'os']
    
    total_items = 0
    results = {}
    
    # 测试各个分类
    for category in categories:
        count = test_single_category(scraper, category)
        results[category] = count
        total_items += count
    
    # 显示总结
    print("\n=== 测试结果总结 ===")
    print(f"总计抓取: {total_items} 条新闻")
    
    category_names = {
        'mobile': '手机',
        'smart_home': '智能家电', 
        'automotive': '汽车',
        'chip': '芯片',
        'os': '操作系统'
    }
    
    for category, count in results.items():
        name = category_names.get(category, category)
        print(f"{name}: {count} 条")
    
    # 测试完整抓取
    print("\n=== 测试完整抓取功能 ===")
    try:
        all_news = scraper.scrape_all_news()
        
        # 保存测试结果
        with open('/workspace/test_results.json', 'w', encoding='utf-8') as f:
            json.dump(all_news, f, ensure_ascii=False, indent=2)
        
        print("完整抓取测试成功!")
        print(f"结果已保存到 test_results.json")
        print(f"总计: {all_news.get('total_items', 0)} 条新闻")
        
    except Exception as e:
        print(f"完整抓取测试失败: {e}")
    
    print("\n测试完成!")

if __name__ == "__main__":
    main()