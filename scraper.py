#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
import json
import time
import re
from urllib.parse import urljoin, urlparse
from datetime import datetime
import logging
from typing import List, Dict, Any
import random
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NewsScraper:
    def __init__(self):
        self.session = requests.Session()
        
        # 设置重试策略
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # 设置请求头
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        # 网站配置
        self.sites_config = {
            'mobile': [
                {
                    'name': 'IT之家',
                    'url': 'https://mobile.ithome.com/',
                    'selector': '.lst li',
                    'title_selector': 'a',
                    'summary_selector': '.c',
                    'link_attr': 'href'
                },
                {
                    'name': '新浪科技',
                    'url': 'https://mobile.sina.com.cn/',
                    'selector': '.feed-card',
                    'title_selector': '.feed-card-title',
                    'summary_selector': '.feed-card-summary',
                    'link_attr': 'href'
                },
                {
                    'name': '36氪',
                    'url': 'https://www.36kr.com/search/articles/%E6%89%8B%E6%9C%BA',
                    'selector': '.search-result-item',
                    'title_selector': '.title',
                    'summary_selector': '.summary',
                    'link_attr': 'href'
                }
            ],
            'smart_home': [
                {
                    'name': '新浪科技',
                    'url': 'https://www.smartcn.cn/news',
                    'selector': '.news-item',
                    'title_selector': '.title',
                    'summary_selector': '.summary',
                    'link_attr': 'href'
                },
                {
                    'name': '36氪',
                    'url': 'https://www.36kr.com/search/articles/%E6%99%BA%E8%83%BD%E5%AE%B6%E7%94%B5',
                    'selector': '.search-result-item',
                    'title_selector': '.title',
                    'summary_selector': '.summary',
                    'link_attr': 'href'
                }
            ],
            'automotive': [
                {
                    'name': '新华网',
                    'url': 'https://www.news.cn/auto/index.html',
                    'selector': '.news-item',
                    'title_selector': '.title',
                    'summary_selector': '.summary',
                    'link_attr': 'href'
                },
                {
                    'name': '36氪',
                    'url': 'https://www.36kr.com/information/travel/',
                    'selector': '.article-item',
                    'title_selector': '.title',
                    'summary_selector': '.summary',
                    'link_attr': 'href'
                }
            ],
            'chip': [
                {
                    'name': '新华网',
                    'url': 'https://so.news.cn/#search/0/%E8%8A%AF%E7%89%87/1/0',
                    'selector': '.result-item',
                    'title_selector': '.title',
                    'summary_selector': '.summary',
                    'link_attr': 'href'
                },
                {
                    'name': 'IT之家',
                    'url': 'https://www.ithome.com/search/%E8%8A%AF%E7%89%87.html',
                    'selector': '.lst li',
                    'title_selector': 'a',
                    'summary_selector': '.c',
                    'link_attr': 'href'
                },
                {
                    'name': '36氪',
                    'url': 'https://www.36kr.com/search/articles/%E8%8A%AF%E7%89%87',
                    'selector': '.search-result-item',
                    'title_selector': '.title',
                    'summary_selector': '.summary',
                    'link_attr': 'href'
                }
            ],
            'os': [
                {
                    'name': '新浪科技',
                    'url': 'https://search.sina.com.cn/?ac=product&from=tech_index&source=tech&range=title&f_name=&col=&c=news&ie=utf-8&c=news&q=%E6%93%8D%E4%BD%9C%E7%B3%BB%E7%BB%9F',
                    'selector': '.result',
                    'title_selector': '.title',
                    'summary_selector': '.summary',
                    'link_attr': 'href'
                },
                {
                    'name': '36氪',
                    'url': 'https://www.36kr.com/search/articles/%E6%93%8D%E4%BD%9C%E7%B3%BB%E7%BB%9F',
                    'selector': '.search-result-item',
                    'title_selector': '.title',
                    'summary_selector': '.summary',
                    'link_attr': 'href'
                }
            ]
        }

    def get_page_content(self, url: str) -> str:
        """获取网页内容"""
        try:
            # 随机延迟，避免被反爬
            time.sleep(random.uniform(1, 3))
            
            response = self.session.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()
            response.encoding = response.apparent_encoding or 'utf-8'
            return response.text
        except requests.RequestException as e:
            logger.error(f"获取网页内容失败 {url}: {e}")
            return ""

    def extract_news_items(self, html: str, config: Dict[str, Any], base_url: str) -> List[Dict[str, Any]]:
        """从HTML中提取新闻条目"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            items = []
            
            # 查找新闻条目
            news_elements = soup.select(config['selector'])
            
            for element in news_elements[:10]:  # 限制每个网站最多10条新闻
                try:
                    # 提取标题
                    title_elem = element.select_one(config['title_selector'])
                    if not title_elem:
                        continue
                    
                    title = title_elem.get_text(strip=True)
                    if not title:
                        continue
                    
                    # 提取链接
                    link_elem = title_elem if title_elem.name == 'a' else title_elem.find('a')
                    if not link_elem:
                        link_elem = element.find('a')
                    
                    if link_elem:
                        link = link_elem.get(config['link_attr'], '')
                        if link:
                            # 处理相对链接
                            link = urljoin(base_url, link)
                    else:
                        link = base_url
                    
                    # 提取摘要
                    summary = ""
                    if config.get('summary_selector'):
                        summary_elem = element.select_one(config['summary_selector'])
                        if summary_elem:
                            summary = summary_elem.get_text(strip=True)
                    
                    # 如果没有摘要，尝试获取第一段文本
                    if not summary:
                        text_elem = element.find(['p', 'div', 'span'])
                        if text_elem:
                            summary = text_elem.get_text(strip=True)[:200] + "..."
                    
                    items.append({
                        'title': title,
                        'url': link,
                        'summary': summary,
                        'source': config['name']
                    })
                    
                except Exception as e:
                    logger.warning(f"提取新闻条目失败: {e}")
                    continue
            
            return items
            
        except Exception as e:
            logger.error(f"解析HTML失败: {e}")
            return []

    def scrape_generic_news(self, url: str, site_name: str) -> List[Dict[str, Any]]:
        """通用新闻抓取方法"""
        try:
            html = self.get_page_content(url)
            if not html:
                return []
            
            soup = BeautifulSoup(html, 'html.parser')
            items = []
            
            # 尝试多种常见的新闻选择器
            selectors = [
                'article', '.article', '.news-item', '.item', '.post',
                'li a', '.title a', 'h3 a', 'h2 a', '.headline a'
            ]
            
            for selector in selectors:
                elements = soup.select(selector)
                if len(elements) > 3:  # 如果找到足够多的元素，使用这个选择器
                    for elem in elements[:10]:
                        try:
                            if elem.name == 'a':
                                title = elem.get_text(strip=True)
                                link = elem.get('href', '')
                            else:
                                link_elem = elem.find('a')
                                if link_elem:
                                    title = link_elem.get_text(strip=True)
                                    link = link_elem.get('href', '')
                                else:
                                    continue
                            
                            if title and link:
                                # 处理相对链接
                                link = urljoin(url, link)
                                
                                # 尝试获取摘要
                                summary = ""
                                parent = elem.parent if elem.name == 'a' else elem
                                if parent:
                                    text_elems = parent.find_all(['p', 'div', 'span'])
                                    for text_elem in text_elems:
                                        text = text_elem.get_text(strip=True)
                                        if len(text) > 20 and text not in title:
                                            summary = text[:200] + "..."
                                            break
                                
                                items.append({
                                    'title': title,
                                    'url': link,
                                    'summary': summary,
                                    'source': site_name
                                })
                        except:
                            continue
                    
                    if items:
                        break
            
            return items[:10]
            
        except Exception as e:
            logger.error(f"通用新闻抓取失败 {url}: {e}")
            return []

    def scrape_category(self, category: str) -> List[Dict[str, Any]]:
        """抓取特定分类的新闻"""
        logger.info(f"开始抓取 {category} 分类新闻")
        all_items = []
        
        if category not in self.sites_config:
            logger.warning(f"未找到 {category} 分类配置")
            return []
        
        for site_config in self.sites_config[category]:
            try:
                logger.info(f"抓取 {site_config['name']} - {site_config['url']}")
                
                # 先尝试使用配置的选择器
                html = self.get_page_content(site_config['url'])
                if html:
                    items = self.extract_news_items(html, site_config, site_config['url'])
                    if not items:
                        # 如果配置的选择器没有找到内容，使用通用方法
                        items = self.scrape_generic_news(site_config['url'], site_config['name'])
                    
                    all_items.extend(items)
                    logger.info(f"从 {site_config['name']} 获取到 {len(items)} 条新闻")
                
            except Exception as e:
                logger.error(f"抓取 {site_config['name']} 失败: {e}")
                continue
        
        # 去重并排序
        unique_items = []
        seen_titles = set()
        
        for item in all_items:
            title_key = item['title'].lower().strip()
            if title_key not in seen_titles:
                seen_titles.add(title_key)
                unique_items.append(item)
        
        logger.info(f"{category} 分类共获取到 {len(unique_items)} 条去重后的新闻")
        return unique_items

    def scrape_all_news(self) -> Dict[str, Any]:
        """抓取所有分类的新闻"""
        logger.info("开始抓取所有新闻")
        start_time = time.time()
        
        results = {}
        categories = ['mobile', 'smart_home', 'automotive', 'chip', 'os']
        
        for category in categories:
            results[category] = self.scrape_category(category)
            # 在分类之间添加延迟
            time.sleep(2)
        
        end_time = time.time()
        logger.info(f"抓取完成，耗时 {end_time - start_time:.2f} 秒")
        
        # 添加时间戳
        results['timestamp'] = datetime.now().isoformat()
        results['total_items'] = sum(len(items) for items in results.values() if isinstance(items, list))
        
        return results

def main():
    """主函数"""
    scraper = NewsScraper()
    
    try:
        # 抓取新闻
        news_data = scraper.scrape_all_news()
        
        # 保存到文件
        with open('/workspace/news_data.json', 'w', encoding='utf-8') as f:
            json.dump(news_data, f, ensure_ascii=False, indent=2)
        
        logger.info("新闻数据已保存到 news_data.json")
        
        # 打印统计信息
        print(f"\n抓取统计:")
        print(f"总计: {news_data.get('total_items', 0)} 条新闻")
        for category, items in news_data.items():
            if isinstance(items, list):
                print(f"{category}: {len(items)} 条")
        
        return news_data
        
    except Exception as e:
        logger.error(f"主程序执行失败: {e}")
        return {}

if __name__ == "__main__":
    main()