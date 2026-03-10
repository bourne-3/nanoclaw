#!/usr/bin/env python3
"""
向本地API发送搜索请求的脚本
"""

import requests
import json
import argparse
import time

def main():
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='向本地API发送搜索请求')
    parser.add_argument(
        '--query',
        type=str,
        required=True,
        help='搜索查询内容 (必填)'
    )
    parser.add_argument(
        '--history',
        type=str,
        help='历史记录 JSON 字符串 (可选)'
    )
    args = parser.parse_args()
    
    # API端点
    url = "http://host.docker.internal:3000/api/search"

    # 请求数据
    payload = {
        "chatModel": {
            "providerId": "4a98bf54-7526-4cf9-91ef-9916b14164d9",
            "key": "Claude-4.5-Sonnet"
        },
        "embeddingModel": {
            "providerId": "1339a12f-3052-4b66-84ad-deb11a6f5549",
            "key": "embeddinggemma:latest"
        },
        "optimizationMode": "balanced", # speed, balanced, quality
        "sources": ["web"],
        "query": args.query,
        "history": json.loads(args.history) if args.history else [],
        "stream": False
    }
    
    # 请求头
    headers = {
        "Content-Type": "application/json"
    }
    
    # 发送请求(超时时间5分钟 = 300秒)
    start_time = time.time()
    elapsed_time = None
    try:
        print(f"正在发送请求...")
        print(f"查询内容: {args.query}")
        response = requests.post(
            url,
            headers=headers,
            data=json.dumps(payload, ensure_ascii=False),
            timeout=300  # 5分钟超时
        )
        elapsed_time = time.time() - start_time
        
        # 检查响应状态
        response.raise_for_status()
        
        # 提取并打印 message 字段
        response_data = response.json()
        print(response_data.get("message", "[ppc 无返回内容]"))
        
    except requests.exceptions.Timeout:
        elapsed_time = time.time() - start_time if elapsed_time is None else elapsed_time
        print(f"错误: 请求超时(超过5分钟), 已耗时: {elapsed_time:.2f} 秒")
    except requests.exceptions.ConnectionError:
        elapsed_time = time.time() - start_time if elapsed_time is None else elapsed_time
        print(f"错误: 无法连接到服务器,请确保 http://host.docker.internal:3000 正在运行, 已耗时: {elapsed_time:.2f} 秒")
    except requests.exceptions.HTTPError as e:
        print(f"HTTP错误: {e}")
        print("响应内容:", response.text)
    except Exception as e:
        elapsed_time = time.time() - start_time
        print(f"发生错误: {type(e).__name__}: {e}, 已耗时: {elapsed_time:.2f} 秒")

if __name__ == "__main__":
    main()
