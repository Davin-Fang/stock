#!/usr/bin/env python3
"""
台灣股票篩選分析工具啟動腳本
"""

import subprocess
import sys
import os
import glob
from datetime import datetime

def check_dependencies():
    """檢查依賴套件"""
    print("🔍 檢查依賴套件...")
    
    required_packages = {
        'streamlit': 'streamlit',
        'pandas': 'pandas',
        'plotly': 'plotly',
        'numpy': 'numpy'
    }
    
    missing_packages = []
    
    for package_name, import_name in required_packages.items():
        try:
            __import__(import_name)
            print(f"✅ {package_name} 已安裝")
        except ImportError:
            print(f"❌ {package_name} 未安裝")
            missing_packages.append(package_name)
    
    if missing_packages:
        print(f"\n❌ 缺少依賴套件: {', '.join(missing_packages)}")
        print("請執行以下命令安裝:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    print("✅ 所有依賴套件已就緒")
    return True

def check_data():
    """檢查數據文件"""
    print("\n🔍 檢查數據文件...")
    
    files = glob.glob('data/processed/stock_data_*.csv')
    
    if not files:
        print("⚠️ 找不到股票數據文件")
        print("正在生成示例數據...")
        
        try:
            subprocess.run([sys.executable, 'create_sample_data.py'], check=True)
            print("✅ 示例數據生成成功")
            return True
        except subprocess.CalledProcessError:
            print("❌ 示例數據生成失敗")
            return False
        except FileNotFoundError:
            print("❌ 找不到 create_sample_data.py 文件")
            return False
    else:
        latest_file = max(files, key=os.path.getctime)
        file_time = datetime.fromtimestamp(os.path.getctime(latest_file))
        print(f"✅ 找到數據文件: {os.path.basename(latest_file)}")
        print(f"📅 最後更新時間: {file_time.strftime('%Y-%m-%d %H:%M:%S')}")
        return True

def run_tests():
    """運行測試"""
    print("\n🧪 運行功能測試...")
    
    try:
        result = subprocess.run([sys.executable, 'test_analyzer.py'], 
                              capture_output=True, text=True, check=True)
        print("✅ 所有測試通過")
        return True
    except subprocess.CalledProcessError as e:
        print("❌ 測試失敗")
        print(e.stdout)
        print(e.stderr)
        return False
    except FileNotFoundError:
        print("⚠️ 找不到測試文件，跳過測試")
        return True

def start_streamlit():
    """啟動 Streamlit 應用"""
    print("\n🚀 啟動台灣股票篩選分析工具...")
    print("📱 應用將在瀏覽器中自動打開 http://localhost:8501")
    print("🛑 按 Ctrl+C 停止應用")
    
    try:
        subprocess.run([
            sys.executable, '-m', 'streamlit', 'run', 
            'taiwan_stock_analyzer.py',
            '--server.port=8501',
            '--server.address=localhost'
        ], check=True)
    except subprocess.CalledProcessError:
        print("❌ Streamlit 啟動失敗")
        return False
    except KeyboardInterrupt:
        print("\n👋 應用已停止")
        return True

def main():
    """主函數"""
    print("🎯 台灣股票篩選分析工具啟動器")
    print("=" * 50)
    
    # 檢查當前工作目錄
    print(f"📂 當前工作目錄: {os.getcwd()}")
    
    # 檢查必要文件
    if not os.path.exists('taiwan_stock_analyzer.py'):
        print("❌ 找不到主程式文件 taiwan_stock_analyzer.py")
        print("請確保在正確的目錄中運行此腳本")
        return
    
    # 檢查依賴套件
    if not check_dependencies():
        print("\n💡 提示: 您可以執行以下命令安裝所有依賴套件:")
        print("pip install -r requirements.txt")
        return
    
    # 檢查數據文件
    if not check_data():
        print("❌ 數據準備失敗")
        return
    
    # 運行測試（可選）
    run_quick_test = input("\n❓ 是否運行快速測試？(y/N): ").strip().lower()
    if run_quick_test in ['y', 'yes']:
        if not run_tests():
            continue_anyway = input("⚠️ 測試失敗，是否仍要繼續啟動？(y/N): ").strip().lower()
            if continue_anyway not in ['y', 'yes']:
                return
    
    print("\n" + "=" * 50)
    
    # 啟動應用
    start_streamlit()

if __name__ == "__main__":
    main() 