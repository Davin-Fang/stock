#!/usr/bin/env python3
"""
生產環境啟動腳本
用於雲端部署的台灣股票篩選分析工具
"""

import os
import sys
import subprocess

def main():
    """啟動 Streamlit 應用程序"""
    
    # 設定環境變量
    os.environ.setdefault('STREAMLIT_SERVER_PORT', os.environ.get('PORT', '8501'))
    os.environ.setdefault('STREAMLIT_SERVER_ADDRESS', '0.0.0.0')
    os.environ.setdefault('STREAMLIT_SERVER_HEADLESS', 'true')
    os.environ.setdefault('STREAMLIT_BROWSER_GATHER_USAGE_STATS', 'false')
    
    # 啟動命令
    cmd = [
        'streamlit', 'run', 'taiwan_stock_analyzer.py',
        '--server.port', os.environ.get('PORT', '8501'),
        '--server.address', '0.0.0.0',
        '--server.headless', 'true',
        '--browser.gatherUsageStats', 'false'
    ]
    
    print(f"🚀 啟動台灣股票篩選工具...")
    print(f"📡 端口: {os.environ.get('PORT', '8501')}")
    print(f"🌐 地址: 0.0.0.0")
    
    # 執行命令
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ 啟動失敗: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("❌ 找不到 streamlit 命令，請確保已安裝 streamlit")
        sys.exit(1)

if __name__ == "__main__":
    main() 