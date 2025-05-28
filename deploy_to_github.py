#!/usr/bin/env python3
"""
台灣股票篩選工具 - GitHub 部署腳本
幫助您將項目部署到 GitHub 並設置 Streamlit Cloud
"""

import os
import subprocess
import sys
import webbrowser
from pathlib import Path

def run_command(cmd, description, capture_output=True):
    """執行命令並處理錯誤"""
    print(f"🔧 {description}...")
    try:
        if capture_output:
            result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        else:
            result = subprocess.run(cmd, shell=True, check=True)
        print(f"✅ {description} 完成")
        return result
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} 失敗: {e}")
        return None

def check_git_config():
    """檢查 Git 配置"""
    print("🔍 檢查 Git 配置...")
    
    try:
        name_result = subprocess.run(['git', 'config', 'user.name'], capture_output=True, text=True)
        email_result = subprocess.run(['git', 'config', 'user.email'], capture_output=True, text=True)
        
        if not name_result.stdout.strip():
            name = input("❓ 請輸入您的 Git 用戶名: ").strip()
            run_command(f'git config --global user.name "{name}"', "設置 Git 用戶名")
        
        if not email_result.stdout.strip():
            email = input("❓ 請輸入您的 Git 郵箱: ").strip()
            run_command(f'git config --global user.email "{email}"', "設置 Git 郵箱")
            
        print(f"✅ Git 用戶: {subprocess.run(['git', 'config', 'user.name'], capture_output=True, text=True).stdout.strip()}")
        print(f"✅ Git 郵箱: {subprocess.run(['git', 'config', 'user.email'], capture_output=True, text=True).stdout.strip()}")
        
    except Exception as e:
        print(f"⚠️ Git 配置檢查失敗: {e}")

def create_github_repo_guide():
    """GitHub 倉庫創建指南"""
    print("\n📝 GitHub 倉庫創建指南:")
    print("=" * 50)
    print("1. 前往 GitHub: https://github.com")
    print("2. 點擊右上角的 '+' 按鈕")
    print("3. 選擇 'New repository'")
    print("4. 設置倉庫信息:")
    print("   - Repository name: taiwan-stock-analyzer (推薦)")
    print("   - Description: 台灣股票篩選分析工具 - Taiwan Stock Screening Tool")
    print("   - 設為 Public (這樣才能使用 Streamlit Cloud 免費部署)")
    print("   - 不要初始化 README (我們已經有了)")
    print("5. 點擊 'Create repository'")
    
    input("\n按 Enter 繼續，當您創建好倉庫後...")
    
    repo_url = input("\n📋 請輸入您剛創建的 GitHub 倉庫 URL (例如: https://github.com/username/taiwan-stock-analyzer.git): ").strip()
    
    if not repo_url:
        print("❌ 請提供有效的倉庫 URL")
        return None
        
    return repo_url

def push_to_github(repo_url):
    """推送代碼到 GitHub"""
    print(f"\n🚀 推送代碼到 GitHub: {repo_url}")
    
    # 添加遠程倉庫
    run_command(f"git remote add origin {repo_url}", "添加遠程倉庫")
    
    # 推送代碼
    result = run_command("git push -u origin main", "推送代碼到 GitHub", capture_output=False)
    
    if result:
        print("🎉 代碼成功推送到 GitHub!")
        return True
    else:
        print("❌ 推送失敗，可能需要身份驗證")
        print("💡 提示:")
        print("   - 確保您已登入 GitHub")
        print("   - 可能需要設置 Personal Access Token")
        print("   - 或使用 GitHub CLI: gh auth login")
        return False

def streamlit_cloud_setup(repo_url):
    """設置 Streamlit Cloud 部署"""
    print("\n☁️ Streamlit Cloud 部署設置:")
    print("=" * 50)
    
    # 提取倉庫信息
    if repo_url.endswith('.git'):
        repo_url = repo_url[:-4]
    
    username = repo_url.split('/')[-2]
    repo_name = repo_url.split('/')[-1]
    
    print(f"📋 您的倉庫信息:")
    print(f"   GitHub 用戶: {username}")
    print(f"   倉庫名稱: {repo_name}")
    
    print("\n🌟 Streamlit Cloud 部署步驟:")
    print("1. 前往: https://share.streamlit.io")
    print("2. 使用 GitHub 帳號登入")
    print("3. 點擊 'New app'")
    print("4. 填入以下信息:")
    print(f"   - Repository: {username}/{repo_name}")
    print("   - Branch: main")
    print("   - Main file path: taiwan_stock_analyzer.py")
    print("5. 點擊 'Deploy!'")
    print("\n⏱️ 部署通常需要 2-5 分鐘")
    print("🔗 完成後您會獲得一個 https://xxx.streamlit.app 的網址")
    
    open_browser = input("\n❓ 是否要自動打開 Streamlit Cloud 網站? (y/N): ").strip().lower()
    if open_browser == 'y':
        webbrowser.open('https://share.streamlit.io')

def main():
    """主函數"""
    print("🎯 台灣股票篩選工具 - GitHub 部署助手")
    print("=" * 50)
    print("🚀 準備將您的股票分析工具部署到 GitHub 和 Streamlit Cloud!")
    print()
    
    # 檢查 Git 配置
    check_git_config()
    
    # 檢查項目文件
    if not Path('taiwan_stock_analyzer.py').exists():
        print("❌ 找不到主應用文件 taiwan_stock_analyzer.py")
        return
    
    print("\n📊 項目文件檢查:")
    files_to_check = [
        'taiwan_stock_analyzer.py',
        'requirements.txt', 
        'README.md',
        '.streamlit/config.toml',
        'data/processed'
    ]
    
    for file in files_to_check:
        if Path(file).exists():
            print(f"✅ {file}")
        else:
            print(f"⚠️ {file} (可選)")
    
    # 創建 GitHub 倉庫指南
    repo_url = create_github_repo_guide()
    if not repo_url:
        return
    
    # 推送到 GitHub
    if push_to_github(repo_url):
        # 設置 Streamlit Cloud
        streamlit_cloud_setup(repo_url)
        
        print("\n🎉 部署完成!")
        print("🔗 您的 GitHub 倉庫:", repo_url)
        print("☁️ 接下來請按照指南設置 Streamlit Cloud")
        print("\n📱 現在全世界的投資者都可以使用您的股票篩選工具了!")
    else:
        print("\n💡 推送失敗時的解決方案:")
        print("1. 手動推送: git push -u origin main")
        print("2. 設置 GitHub CLI: gh auth login")
        print("3. 或使用 GitHub Desktop")

if __name__ == "__main__":
    main() 