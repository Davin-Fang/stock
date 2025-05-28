#!/usr/bin/env python3
"""
台灣股票篩選工具 - 自動化部署腳本
支持多個雲端平台的一鍵部署
"""

import os
import subprocess
import sys
from pathlib import Path

def run_command(cmd, description):
    """執行命令並處理錯誤"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} 完成")
        return result
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} 失敗: {e}")
        if e.stdout:
            print(f"輸出: {e.stdout}")
        if e.stderr:
            print(f"錯誤: {e.stderr}")
        return None

def check_git():
    """檢查 Git 是否已初始化"""
    if not Path('.git').exists():
        print("📂 初始化 Git 倉庫...")
        run_command("git init", "Git 初始化")
        
def prepare_files():
    """準備部署所需的文件"""
    print("📋 檢查部署文件...")
    
    required_files = [
        'taiwan_stock_analyzer.py',
        'requirements.txt',
        'README.md',
        'Procfile',
        '.streamlit/config.toml'
    ]
    
    missing_files = []
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
    
    if missing_files:
        print(f"⚠️ 缺少文件: {missing_files}")
        return False
    
    print("✅ 所有必需文件都存在")
    return True

def generate_sample_data():
    """生成示例數據"""
    if not Path('data/processed').exists():
        print("📊 生成示例數據...")
        if Path('create_sample_data.py').exists():
            run_command("python create_sample_data.py", "生成示例數據")
        else:
            print("⚠️ 找不到 create_sample_data.py，請手動準備數據文件")

def git_operations():
    """執行 Git 操作"""
    print("📤 準備 Git 提交...")
    
    # 添加所有文件
    run_command("git add .", "添加文件到 Git")
    
    # 檢查是否有更改
    result = run_command("git status --porcelain", "檢查 Git 狀態")
    if result and result.stdout.strip():
        # 有更改，進行提交
        commit_msg = input("💬 請輸入提交訊息 (直接按 Enter 使用默認訊息): ").strip()
        if not commit_msg:
            commit_msg = "部署台灣股票篩選工具"
        
        run_command(f'git commit -m "{commit_msg}"', "Git 提交")
    else:
        print("ℹ️ 沒有新的更改需要提交")

def show_deployment_options():
    """顯示部署選項"""
    print("\n🚀 選擇部署平台:")
    print("1. Streamlit Cloud (推薦 - 完全免費)")
    print("2. Railway (免費層)")
    print("3. Render (免費層)")
    print("4. 只準備文件，手動部署")
    print("5. 查看部署指南")
    
    choice = input("\n請選擇 (1-5): ").strip()
    return choice

def streamlit_cloud_guide():
    """Streamlit Cloud 部署指南"""
    print("\n🌟 Streamlit Cloud 部署步驟:")
    print("1. 推送代碼到 GitHub:")
    
    remote_url = input("   請輸入您的 GitHub 倉庫 URL (例: https://github.com/username/repo.git): ").strip()
    if remote_url:
        run_command(f"git remote add origin {remote_url}", "添加 GitHub 遠程倉庫")
        run_command("git branch -M main", "設置主分支")
        run_command("git push -u origin main", "推送到 GitHub")
    
    print("\n2. 前往 Streamlit Cloud:")
    print("   🔗 https://share.streamlit.io")
    print("3. 點擊 'New app'")
    print("4. 連接您的 GitHub 倉庫")
    print("5. 設置:")
    print("   - Repository: 您的倉庫名稱")
    print("   - Branch: main")
    print("   - Main file path: taiwan_stock_analyzer.py")
    print("6. 點擊 'Deploy!'")
    print("\n🎉 完成！您的應用將在幾分鐘內上線")

def railway_guide():
    """Railway 部署指南"""
    print("\n🚂 Railway 部署步驟:")
    print("1. 前往 Railway: https://railway.app")
    print("2. 使用 GitHub 登入")
    print("3. 點擊 'New Project' → 'Deploy from GitHub repo'")
    print("4. 選擇您的倉庫")
    print("5. Railway 會自動檢測並部署")
    print("6. 等待部署完成，獲取公開 URL")

def render_guide():
    """Render 部署指南"""
    print("\n🎨 Render 部署步驟:")
    print("1. 前往 Render: https://render.com")
    print("2. 創建帳號並連接 GitHub")
    print("3. 點擊 'New' → 'Web Service'")
    print("4. 選擇您的倉庫")
    print("5. 設置:")
    print("   - Build Command: pip install -r requirements.txt")
    print("   - Start Command: streamlit run taiwan_stock_analyzer.py --server.port=$PORT --server.address=0.0.0.0")
    print("6. 點擊 'Create Web Service'")

def main():
    """主函數"""
    print("🎯 台灣股票篩選工具 - 部署助手")
    print("=" * 50)
    
    # 檢查基本環境
    check_git()
    
    if not prepare_files():
        print("❌ 請先準備必要的文件")
        return
    
    # 生成示例數據
    generate_sample_data()
    
    # Git 操作
    git_operations()
    
    # 選擇部署方式
    while True:
        choice = show_deployment_options()
        
        if choice == '1':
            streamlit_cloud_guide()
            break
        elif choice == '2':
            railway_guide()
            break
        elif choice == '3':
            render_guide()
            break
        elif choice == '4':
            print("✅ 文件已準備完成，您可以手動部署到任何平台")
            break
        elif choice == '5':
            print("📖 詳細部署指南請查看 DEPLOYMENT_GUIDE.md")
            break
        else:
            print("❌ 無效選擇，請重新選擇")

if __name__ == "__main__":
    main() 