#!/usr/bin/env python3
"""
台灣股票篩選分析工具測試腳本
"""

import pandas as pd
import os
import sys
from datetime import datetime

def test_data_loading():
    """測試數據載入功能"""
    print("🧪 測試數據載入功能...")
    
    # 檢查數據文件是否存在
    import glob
    files = glob.glob('data/processed/stock_data_*.csv')
    
    if not files:
        print("❌ 找不到股票數據文件")
        return False
    
    latest_file = max(files, key=os.path.getctime)
    print(f"✅ 找到數據文件: {os.path.basename(latest_file)}")
    
    try:
        df = pd.read_csv(latest_file)
        required_columns = ['stock_code', 'name', 'ROE', 'EPS', '年營收成長率', '月營收成長率']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            print(f"❌ 缺少必要欄位: {missing_columns}")
            return False
        
        print(f"✅ 數據載入成功，包含 {len(df)} 支股票")
        print(f"✅ 所有必要欄位都存在: {required_columns}")
        return True, df
        
    except Exception as e:
        print(f"❌ 數據載入失敗: {str(e)}")
        return False

def test_filtering_logic(df):
    """測試篩選邏輯"""
    print("\n🧪 測試篩選邏輯...")
    
    try:
        # 清理數據
        for col in ['ROE', 'EPS', '年營收成長率', '月營收成長率']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        df_clean = df.dropna(subset=['ROE', 'EPS', '年營收成長率', '月營收成長率'])
        print(f"✅ 數據清理完成，剩餘 {len(df_clean)} 支股票")
        
        # 測試不同的篩選條件
        test_cases = [
            {"name": "寬鬆條件", "roe": 5, "eps": 0, "annual": 0, "monthly": 0},
            {"name": "中等條件", "roe": 10, "eps": 1, "annual": 10, "monthly": 10},
            {"name": "嚴格條件", "roe": 15, "eps": 2, "annual": 20, "monthly": 20},
            {"name": "極嚴格條件", "roe": 25, "eps": 5, "annual": 50, "monthly": 50}
        ]
        
        for case in test_cases:
            filtered = df_clean[
                (df_clean['ROE'] > case['roe']) &
                (df_clean['EPS'] > case['eps']) &
                (df_clean['年營收成長率'] > case['annual']) &
                (df_clean['月營收成長率'] > case['monthly'])
            ]
            
            print(f"✅ {case['name']} (ROE>{case['roe']}%, EPS>{case['eps']}, 年成長>{case['annual']}%, 月成長>{case['monthly']}%): {len(filtered)} 支股票")
        
        return True
        
    except Exception as e:
        print(f"❌ 篩選邏輯測試失敗: {str(e)}")
        return False

def test_data_statistics(df):
    """測試數據統計功能"""
    print("\n🧪 測試數據統計功能...")
    
    try:
        # 清理數據
        for col in ['ROE', 'EPS', '年營收成長率', '月營收成長率']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        df_clean = df.dropna(subset=['ROE', 'EPS', '年營收成長率', '月營收成長率'])
        
        # 計算統計指標
        stats = {
            'ROE': {'min': df_clean['ROE'].min(), 'max': df_clean['ROE'].max(), 'mean': df_clean['ROE'].mean()},
            'EPS': {'min': df_clean['EPS'].min(), 'max': df_clean['EPS'].max(), 'mean': df_clean['EPS'].mean()},
            '年營收成長率': {'min': df_clean['年營收成長率'].min(), 'max': df_clean['年營收成長率'].max(), 'mean': df_clean['年營收成長率'].mean()},
            '月營收成長率': {'min': df_clean['月營收成長率'].min(), 'max': df_clean['月營收成長率'].max(), 'mean': df_clean['月營收成長率'].mean()}
        }
        
        print("✅ 數據統計:")
        for metric, values in stats.items():
            print(f"   {metric}: 最小值={values['min']:.2f}, 最大值={values['max']:.2f}, 平均值={values['mean']:.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ 數據統計測試失敗: {str(e)}")
        return False

def test_export_functionality(df):
    """測試數據匯出功能"""
    print("\n🧪 測試數據匯出功能...")
    
    try:
        # 清理數據
        for col in ['ROE', 'EPS', '年營收成長率', '月營收成長率']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        df_clean = df.dropna(subset=['ROE', 'EPS', '年營收成長率', '月營收成長率'])
        
        # 篩選一些股票
        df_filtered = df_clean[
            (df_clean['ROE'] > 10) &
            (df_clean['EPS'] > 0) &
            (df_clean['年營收成長率'] > 0) &
            (df_clean['月營收成長率'] > 0)
        ]
        
        # 測試匯出
        test_filename = f"test_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df_filtered.to_csv(test_filename, index=False, encoding='utf-8-sig')
        
        # 檢查文件是否成功創建
        if os.path.exists(test_filename):
            file_size = os.path.getsize(test_filename)
            print(f"✅ 數據匯出成功: {test_filename} ({file_size} bytes)")
            
            # 清理測試文件
            try:
                os.remove(test_filename)
                print("✅ 測試文件已清理")
            except Exception as e:
                print(f"⚠️ 測試文件清理失敗: {e}")
            return True
        else:
            print("❌ 匯出文件未生成")
            return False
            
    except Exception as e:
        print(f"❌ 數據匯出測試失敗: {str(e)}")
        return False

def main():
    """主測試函數"""
    print("🚀 開始台灣股票篩選分析工具測試")
    print("=" * 50)
    
    all_tests_passed = True
    
    # 測試數據載入
    result = test_data_loading()
    if isinstance(result, tuple):
        success, df = result
        if not success:
            all_tests_passed = False
            print("❌ 數據載入測試失敗，跳過後續測試")
            return
    else:
        all_tests_passed = False
        print("❌ 數據載入測試失敗，跳過後續測試")
        return
    
    # 測試篩選邏輯
    if not test_filtering_logic(df):
        all_tests_passed = False
    
    # 測試數據統計
    if not test_data_statistics(df):
        all_tests_passed = False
    
    # 測試匯出功能
    if not test_export_functionality(df):
        all_tests_passed = False
    
    # 總結
    print("\n" + "=" * 50)
    if all_tests_passed:
        print("🎉 所有測試通過！股票分析工具功能正常")
        print("\n📋 使用說明:")
        print("1. 執行 'streamlit run taiwan_stock_analyzer.py' 啟動應用")
        print("2. 在瀏覽器中打開 http://localhost:8501")
        print("3. 調整左側邊欄的篩選條件")
        print("4. 查看篩選結果和統計圖表")
    else:
        print("❌ 部分測試失敗，請檢查錯誤訊息並修正")
    
    print("\n🔍 Debug 資訊:")
    print(f"- 當前工作目錄: {os.getcwd()}")
    print(f"- Python 版本: {sys.version}")
    print(f"- Pandas 版本: {pd.__version__}")

if __name__ == "__main__":
    main() 