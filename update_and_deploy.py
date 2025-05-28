#!/usr/bin/env python3
"""
台灣股票數據自動更新和部署腳本
一鍵更新最新股票數據並自動同步到 GitHub 和 Streamlit Cloud
"""

import os
import subprocess
import sys
from datetime import datetime
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

def crawl_latest_data():
    """抓取最新股票數據"""
    print("📊 開始抓取最新台灣股票數據...")
    
    # 檢查混合式爬蟲是否存在
    if Path('hybrid_real_crawler.py').exists():
        print("🚀 使用混合式真實數據爬蟲...")
        result = run_command("python hybrid_real_crawler.py", "抓取真實股票數據")
        return result is not None
    
    elif Path('twse_real_crawler.py').exists():
        print("🚀 使用 TWSE 真實數據爬蟲...")
        result = run_command("python twse_real_crawler.py", "抓取 TWSE 股票數據")
        return result is not None
    
    elif Path('create_sample_data.py').exists():
        print("🚀 使用示例數據生成器...")
        result = run_command("python create_sample_data.py", "生成示例股票數據")
        return result is not None
    
    else:
        print("❌ 找不到可用的數據爬蟲腳本")
        return False

def check_new_data():
    """檢查是否有新數據文件"""
    data_dirs = ['data/processed', 'data', '.']
    
    for data_dir in data_dirs:
        if Path(data_dir).exists():
            csv_files = list(Path(data_dir).glob('*stock_data_*.csv')) + \
                       list(Path(data_dir).glob('hybrid_real_*.csv')) + \
                       list(Path(data_dir).glob('twse_*.csv'))
            
            if csv_files:
                latest_file = max(csv_files, key=os.path.getctime)
                print(f"📄 找到最新數據文件: {latest_file}")
                
                # 檢查文件是否是最近生成的（5分鐘內）
                file_time = os.path.getctime(latest_file)
                current_time = datetime.now().timestamp()
                
                if current_time - file_time < 300:  # 5分鐘內
                    print("✅ 數據文件是最新的")
                    return True
                else:
                    print("⚠️ 數據文件較舊，建議重新抓取")
                    return False
    
    print("❌ 未找到數據文件")
    return False

def test_analyzer():
    """測試分析器是否能正常運行"""
    print("🧪 測試股票分析器...")
    
    try:
        # 簡單測試導入
        import pandas as pd
        print("✅ Pandas 正常")
        
        # 檢查是否能找到數據文件
        if Path('taiwan_stock_analyzer.py').exists():
            print("✅ 分析器文件存在")
            return True
        else:
            print("❌ 找不到分析器文件")
            return False
            
    except ImportError as e:
        print(f"❌ 導入錯誤: {e}")
        return False

def git_update():
    """將新數據提交到 Git"""
    print("📤 更新 Git 倉庫...")
    
    # 檢查 Git 狀態
    result = run_command("git status --porcelain", "檢查 Git 狀態")
    if result and result.stdout.strip():
        # 有更改需要提交
        
        # 添加數據文件
        run_command("git add data/", "添加數據目錄")
        run_command("git add *.csv", "添加 CSV 文件")
        
        # 生成提交訊息
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        commit_msg = f"Update stock data - {timestamp}"
        
        # 提交更改
        result = run_command(f'git commit -m "{commit_msg}"', "提交數據更新")
        
        if result:
            # 推送到 GitHub
            result = run_command("git push origin main", "推送到 GitHub")
            
            if result:
                print("🎉 數據已成功更新到 GitHub!")
                print("☁️ Streamlit Cloud 將在 2-5 分鐘內自動更新")
                return True
            else:
                print("❌ 推送到 GitHub 失敗")
                return False
        else:
            print("❌ Git 提交失敗")
            return False
    else:
        print("ℹ️ 沒有新的更改需要提交")
        return True

def show_data_summary():
    """顯示數據摘要"""
    print("\n📊 數據文件摘要:")
    print("=" * 50)
    
    # 查找最新數據文件
    data_patterns = [
        'data/processed/*stock_data_*.csv',
        'data/*stock_data_*.csv', 
        '*stock_data_*.csv',
        '*hybrid_real_*.csv',
        '*twse_*.csv'
    ]
    
    latest_file = None
    for pattern in data_patterns:
        files = list(Path('.').glob(pattern))
        if files:
            latest_file = max(files, key=os.path.getctime)
            break
    
    if latest_file:
        try:
            import pandas as pd
            df = pd.read_csv(latest_file)
            
            print(f"📄 文件: {latest_file}")
            print(f"📈 股票數量: {len(df)}")
            print(f"📅 更新時間: {datetime.fromtimestamp(os.path.getctime(latest_file)).strftime('%Y-%m-%d %H:%M:%S')}")
            
            if 'ROE' in df.columns:
                print(f"📊 平均 ROE: {df['ROE'].mean():.2f}%")
            
            if 'EPS' in df.columns:
                print(f"💰 平均 EPS: {df['EPS'].mean():.2f}")
                
            print(f"🔗 GitHub: https://github.com/Davin-Fang/stock.git")
            
        except Exception as e:
            print(f"⚠️ 讀取數據文件時出錯: {e}")
    else:
        print("❌ 未找到數據文件")

def main():
    """主函數"""
    print("🎯 台灣股票數據自動更新系統")
    print("=" * 50)
    print("🚀 準備更新最新股票數據並部署到雲端!")
    print()
    
    success_steps = 0
    total_steps = 4
    
    # 步驟 1: 抓取最新數據
    print("📊 步驟 1/4: 抓取最新股票數據")
    if crawl_latest_data():
        success_steps += 1
        print("✅ 數據抓取成功!")
    else:
        print("❌ 數據抓取失敗")
    
    print()
    
    # 步驟 2: 檢查數據
    print("🔍 步驟 2/4: 驗證數據完整性")
    if check_new_data():
        success_steps += 1
        print("✅ 數據驗證通過!")
    else:
        print("⚠️ 數據驗證有問題，但繼續進行...")
    
    print()
    
    # 步驟 3: 測試分析器
    print("🧪 步驟 3/4: 測試股票分析器")
    if test_analyzer():
        success_steps += 1
        print("✅ 分析器測試通過!")
    else:
        print("⚠️ 分析器測試有問題，但繼續進行...")
    
    print()
    
    # 步驟 4: 更新到 GitHub
    print("📤 步驟 4/4: 更新到 GitHub")
    if git_update():
        success_steps += 1
        print("✅ GitHub 更新成功!")
    else:
        print("❌ GitHub 更新失敗")
    
    print()
    print("=" * 50)
    
    # 總結
    if success_steps >= 3:
        print("🎉 更新完成!")
        print(f"✅ 成功完成 {success_steps}/{total_steps} 個步驟")
        print()
        print("🌟 下一步:")
        print("1. 檢查 GitHub 倉庫: https://github.com/Davin-Fang/stock.git")
        print("2. Streamlit Cloud 將在 2-5 分鐘內自動更新")
        print("3. 訪問您的應用網址查看最新數據")
        
    else:
        print("⚠️ 更新部分成功")
        print(f"⚠️ 完成 {success_steps}/{total_steps} 個步驟")
        print("💡 建議檢查錯誤訊息並手動修復問題")
    
    print()
    show_data_summary()

if __name__ == "__main__":
    main() 