#!/usr/bin/env python3
"""
簡單的股票數據更新腳本
避免編碼問題，專注於數據更新
"""

import os
import sys
import subprocess
import glob
from datetime import datetime
from pathlib import Path

def run_command(cmd, description):
    """執行命令並處理錯誤"""
    print(f"[INFO] {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"[SUCCESS] {description} 完成")
        return result
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] {description} 失敗: {e}")
        if e.stdout:
            print(f"輸出: {e.stdout}")
        if e.stderr:
            print(f"錯誤: {e.stderr}")
        return None

def check_data_files():
    """檢查現有數據文件"""
    print("\n[INFO] 檢查現有數據文件...")
    
    data_patterns = [
        'data/processed/*stock_data_*.csv',
        'data/*stock_data_*.csv', 
        '*stock_data_*.csv',
        '*hybrid_real_*.csv',
        '*twse_*.csv'
    ]
    
    latest_file = None
    for pattern in data_patterns:
        files = glob.glob(pattern)
        if files:
            latest_file = max(files, key=os.path.getctime)
            break
    
    if latest_file:
        file_time = os.path.getctime(latest_file)
        file_date = datetime.fromtimestamp(file_time).strftime('%Y-%m-%d %H:%M:%S')
        print(f"[INFO] 找到最新數據文件: {latest_file}")
        print(f"[INFO] 更新時間: {file_date}")
        
        # 檢查是否為最近文件（24小時內）
        current_time = datetime.now().timestamp()
        if current_time - file_time < 86400:  # 24小時
            print("[INFO] 數據文件較新，無需更新")
            return True
        else:
            print("[INFO] 數據文件較舊，建議更新")
            return False
    else:
        print("[WARNING] 未找到數據文件")
        return False

def update_data():
    """更新股票數據"""
    print("\n[INFO] 開始更新股票數據...")
    
    # 嘗試不同的數據更新方法
    update_methods = [
        ("python demo_data_generator.py", "生成示例數據"),
        ("python quick_data_generator.py", "快速生成數據"),
        ("python twse_data_downloader.py", "下載TWSE數據")
    ]
    
    for cmd, desc in update_methods:
        print(f"\n[INFO] 嘗試方法: {desc}")
        result = run_command(cmd, desc)
        if result:
            print(f"[SUCCESS] {desc} 成功")
            return True
        else:
            print(f"[WARNING] {desc} 失敗，嘗試下一個方法")
    
    print("[ERROR] 所有數據更新方法都失敗了")
    return False

def git_update():
    """更新Git倉庫"""
    print("\n[INFO] 更新Git倉庫...")
    
    # 檢查Git狀態
    result = run_command("git status --porcelain", "檢查Git狀態")
    if result and result.stdout.strip():
        # 有更改需要提交
        run_command("git add .", "添加所有文件")
        
        # 生成提交訊息
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        commit_msg = f"Update stock data - {timestamp}"
        
        # 提交更改
        result = run_command(f'git commit -m "{commit_msg}"', "提交數據更新")
        
        if result:
            # 推送到GitHub
            result = run_command("git push origin main", "推送到GitHub")
            
            if result:
                print("[SUCCESS] 數據已成功更新到GitHub!")
                print("[INFO] Streamlit Cloud將在2-5分鐘內自動更新")
                return True
            else:
                print("[ERROR] 推送到GitHub失敗")
                return False
        else:
            print("[ERROR] Git提交失敗")
            return False
    else:
        print("[INFO] 沒有新的更改需要提交")
        return True

def show_summary():
    """顯示更新摘要"""
    print("\n[INFO] 數據更新摘要:")
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
        files = glob.glob(pattern)
        if files:
            latest_file = max(files, key=os.path.getctime)
            break
    
    if latest_file:
        try:
            import pandas as pd
            df = pd.read_csv(latest_file)
            
            print(f"[INFO] 文件: {latest_file}")
            print(f"[INFO] 股票數量: {len(df)}")
            print(f"[INFO] 更新時間: {datetime.fromtimestamp(os.path.getctime(latest_file)).strftime('%Y-%m-%d %H:%M:%S')}")
            
            if 'ROE' in df.columns:
                print(f"[INFO] 平均ROE: {df['ROE'].mean():.2f}%")
            
            if 'EPS' in df.columns:
                print(f"[INFO] 平均EPS: {df['EPS'].mean():.2f}")
                
            print(f"[INFO] GitHub: https://github.com/Davin-Fang/stock.git")
            
        except Exception as e:
            print(f"[WARNING] 讀取數據文件時出錯: {e}")
    else:
        print("[ERROR] 未找到數據文件")

def main():
    """主函數"""
    print("台灣股票數據更新系統")
    print("=" * 50)
    print("準備更新最新股票數據並部署到雲端!")
    print()
    
    success_steps = 0
    total_steps = 3
    
    # 步驟1: 檢查現有數據
    print(f"\n步驟 1/{total_steps}: 檢查現有數據")
    if check_data_files():
        print("[INFO] 數據較新，跳過更新")
        success_steps += 1
    else:
        # 步驟2: 更新數據
        print(f"\n步驟 2/{total_steps}: 更新數據")
        if update_data():
            success_steps += 1
        else:
            print("[WARNING] 數據更新失敗，但繼續進行")
    
    # 步驟3: Git更新
    print(f"\n步驟 3/{total_steps}: 更新Git")
    if git_update():
        success_steps += 1
    
    # 顯示結果
    print("\n" + "=" * 50)
    if success_steps == total_steps:
        print("[SUCCESS] 所有步驟都成功完成!")
    elif success_steps >= 2:
        print("[PARTIAL] 部分步驟成功完成")
    else:
        print("[ERROR] 大部分步驟失敗")
    
    print(f"[INFO] 完成 {success_steps}/{total_steps} 個步驟")
    
    # 顯示摘要
    show_summary()

if __name__ == "__main__":
    main() 