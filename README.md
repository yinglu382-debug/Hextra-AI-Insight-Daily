# 宏观经济研究 - 科技资讯聚合平台

一个实时抓取和展示科技资讯的Web应用，自动从多个知名科技网站获取最新资讯，并按照手机、智能家电、汽车、操作系统、芯片五个分类进行整理展示。

## 功能特点

- 🔄 **自动更新**: 每小时自动更新一次内容
- 📱 **多分类展示**: 手机、智能家电、汽车、操作系统、芯片五大分类
- 🌐 **多源抓取**: 从IT之家、新浪科技、36氪、新华网等多个网站抓取
- 🎨 **美观界面**: 现代化响应式设计，支持移动端
- 🔗 **直链跳转**: 点击标题直接跳转到原文
- ⚡ **实时刷新**: 支持手动刷新获取最新内容

## 抓取网站

### 手机分类
- IT之家: https://mobile.ithome.com/
- 新浪科技: https://mobile.sina.com.cn/
- 36氪: https://www.36kr.com/search/articles/手机

### 智能家电分类
- 新浪科技: https://www.smartcn.cn/news
- 36氪: https://www.36kr.com/search/articles/智能家电

### 汽车分类
- 新华网: https://www.news.cn/auto/index.html
- 36氪: https://www.36kr.com/information/travel/

### 芯片分类
- 新华网: https://so.news.cn/#search/0/芯片/1/0
- IT之家: https://www.ithome.com/search/芯片.html
- 36氪: https://www.36kr.com/search/articles/芯片

### 操作系统分类
- 新浪科技: https://search.sina.com.cn/?ac=product&from=tech_index&source=tech&range=title&f_name=&col=&c=news&ie=utf-8&c=news&q=操作系统
- 36氪: https://www.36kr.com/search/articles/操作系统

## 快速开始

### 方法一：使用启动脚本（推荐）

```bash
# 运行启动脚本
./start.sh
```

### 方法二：手动启动

1. **安装依赖**
```bash
pip3 install -r requirements.txt
```

2. **启动服务**
```bash
python3 app.py
```

3. **访问网站**
打开浏览器访问: http://localhost:5000

## 项目结构

```
workspace/
├── app.py              # Flask后端服务器
├── scraper.py          # 网页抓取脚本
├── index.html          # 前端页面
├── requirements.txt    # Python依赖
├── start.sh           # 启动脚本
├── README.md          # 说明文档
└── news_data.json     # 新闻数据缓存（自动生成）
```

## 技术架构

### 后端
- **Flask**: Web框架
- **requests + BeautifulSoup**: 网页抓取
- **schedule**: 定时任务
- **threading**: 多线程处理

### 前端
- **原生HTML/CSS/JavaScript**: 轻量级前端
- **Font Awesome**: 图标库
- **响应式设计**: 支持移动端

### 数据流程
1. **定时抓取**: 每小时自动执行抓取任务
2. **数据处理**: 清洗、去重、分类整理
3. **缓存存储**: 保存到JSON文件
4. **API服务**: 通过REST API提供数据
5. **前端展示**: 动态加载和展示内容

## API接口

### GET /api/news
获取所有分类的新闻数据

**响应示例:**
```json
{
  "mobile": [
    {
      "title": "新闻标题",
      "url": "原文链接",
      "summary": "内容摘要",
      "source": "来源网站"
    }
  ],
  "smart_home": [...],
  "automotive": [...],
  "chip": [...],
  "os": [...],
  "last_update": "2024-01-01T12:00:00",
  "total_items": 50
}
```

### GET /api/status
获取系统状态信息

### GET /api/update
手动触发更新任务

## 配置说明

### 更新频率
默认每小时更新一次，可在 `app.py` 中修改：
```python
# 修改这行来改变更新频率
schedule.every().hour.do(update_news_data)
```

### 抓取数量
默认每个网站最多抓取10条新闻，可在 `scraper.py` 中修改：
```python
# 修改这个数字来改变抓取数量
for element in news_elements[:10]:
```

### 网站配置
可在 `scraper.py` 的 `sites_config` 中添加或修改网站配置。

## 部署说明

### 本地部署
按照"快速开始"部分的说明即可。

### 服务器部署
1. 上传项目文件到服务器
2. 安装Python3和pip3
3. 运行启动脚本或手动启动
4. 配置反向代理（可选）

### Docker部署
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5000

CMD ["python", "app.py"]
```

## 注意事项

1. **网络要求**: 需要能够访问目标网站
2. **反爬策略**: 已内置随机延迟和重试机制
3. **资源消耗**: 抓取任务会消耗一定的CPU和网络资源
4. **数据时效**: 数据会缓存到本地，断网时仍可查看缓存内容
5. **合规使用**: 请遵守目标网站的robots.txt和使用条款

## 故障排除

### 常见问题

**Q: 启动后无法访问页面**
A: 检查5000端口是否被占用，确保防火墙允许访问

**Q: 抓取不到内容**
A: 检查网络连接，某些网站可能有反爬措施

**Q: 页面显示"加载失败"**
A: 等待首次抓取完成，或检查后端日志

### 日志查看
运行时会在控制台输出详细日志，包括：
- 抓取进度
- 错误信息
- 统计数据

## 开发说明

### 添加新网站
1. 在 `scraper.py` 的 `sites_config` 中添加配置
2. 测试抓取效果
3. 重启服务

### 修改界面
编辑 `index.html` 中的CSS和JavaScript部分。

### 扩展功能
- 添加新的分类
- 实现数据库存储
- 添加用户管理
- 实现推送通知

## 许可证

本项目仅供学习和研究使用，请遵守相关法律法规和网站使用条款。

## 联系方式

如有问题或建议，请提交Issue或Pull Request。