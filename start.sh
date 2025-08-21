#!/bin/bash

echo "=== 宏观经济研究 - 科技资讯聚合平台 ==="
echo "正在启动服务..."

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python3，请先安装Python3"
    exit 1
fi

# 检查pip是否安装
if ! command -v pip3 &> /dev/null; then
    echo "错误: 未找到pip3，请先安装pip3"
    exit 1
fi

# 安装依赖
echo "正在安装Python依赖包..."
pip3 install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "错误: 依赖安装失败"
    exit 1
fi

# 启动应用
echo "正在启动Web服务器..."
echo "服务将在 http://localhost:5000 启动"
echo "按 Ctrl+C 停止服务"
echo "================================"

python3 app.py