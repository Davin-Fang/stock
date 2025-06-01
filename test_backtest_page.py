#!/usr/bin/env python3
"""
測試批量回測結果頁面功能
"""

import pandas as pd
import glob
import os
from datetime import datetime

def test_backtest_results_loading():
    """測試回測結果載入功能"""
    print("🧪 測試批量回測結果載入功能")
    print("="*50)
    
    # 檢查回測結果文件
    full_files = glob.glob('backtest_results_full_*.csv')
    profitable_files = glob.glob('backtest_results_profitable_*.csv')
    
    print(f"📊 找到完整結果文件: {len(full_files)} 個")
    for file in full_files:
        print(f"  - {file}")
    
    print(f"🎯 找到優質股票文件: {len(profitable_files)} 個")
    for file in profitable_files:
        print(f"  - {file}")
    
    if not full_files:
        print("❌ 沒有找到回測結果文件")
        return False
    
    # 載入最新的結果
    latest_full = max(full_files, key=os.path.getctime)
    latest_profitable = max(profitable_files, key=os.path.getctime) if profitable_files else None
    
    print(f"\n📈 載入最新完整結果: {latest_full}")
    if latest_profitable:
        print(f"🏆 載入最新優質股票: {latest_profitable}")
    
    try:
        full_df = pd.read_csv(latest_full)
        profitable_df = pd.read_csv(latest_profitable) if latest_profitable else pd.DataFrame()
        
        print(f"\n✅ 成功載入數據")
        print(f"📊 完整結果: {len(full_df)} 支股票")
        print(f"🎯 優質股票: {len(profitable_df)} 支股票")
        
        # 基本統計
        print(f"\n📈 基本統計:")
        print(f"平均報酬率: {full_df['total_return'].mean():.2f}%")
        print(f"最高報酬率: {full_df['total_return'].max():.2f}%")
        print(f"最低報酬率: {full_df['total_return'].min():.2f}%")
        print(f"勝率: {len(full_df[full_df['total_return'] > 0]) / len(full_df) * 100:.1f}%")
        
        # 分類統計
        if len(profitable_df) > 0:
            super_high = len(profitable_df[profitable_df['total_return'] > 50])
            high_return = len(profitable_df[(profitable_df['total_return'] >= 30) & (profitable_df['total_return'] <= 50)])
            medium_return = len(profitable_df[(profitable_df['total_return'] >= 20) & (profitable_df['total_return'] < 30)])
            stable_return = len(profitable_df[(profitable_df['total_return'] >= 10) & (profitable_df['total_return'] < 20)])
            
            print(f"\n🏆 優質股票分類:")
            print(f"超高報酬 (>50%): {super_high} 支")
            print(f"高報酬 (30-50%): {high_return} 支")
            print(f"中等報酬 (20-30%): {medium_return} 支")
            print(f"穩健報酬 (10-20%): {stable_return} 支")
        
        return True
        
    except Exception as e:
        print(f"❌ 載入數據失敗: {str(e)}")
        return False

def test_streamlit_imports():
    """測試Streamlit相關導入"""
    print("\n🧪 測試Streamlit相關導入")
    print("="*50)
    
    try:
        import streamlit as st
        print("✅ Streamlit 導入成功")
        
        import plotly.graph_objects as go
        print("✅ Plotly 導入成功")
        
        import plotly.express as px
        print("✅ Plotly Express 導入成功")
        
        return True
        
    except ImportError as e:
        print(f"❌ 導入失敗: {str(e)}")
        return False

def test_app_structure():
    """測試應用結構"""
    print("\n🧪 測試應用結構")
    print("="*50)
    
    # 檢查主應用文件
    if os.path.exists('stock_strategy_app.py'):
        print("✅ 主應用文件存在")
        
        # 檢查是否包含新的頁面函數
        with open('stock_strategy_app.py', 'r', encoding='utf-8') as f:
            content = f.read()
            
        if 'show_backtest_results' in content:
            print("✅ 批量回測結果頁面函數存在")
        else:
            print("❌ 批量回測結果頁面函數不存在")
            return False
            
        if '🎯 批量回測結果' in content:
            print("✅ 頁面選項已添加")
        else:
            print("❌ 頁面選項未添加")
            return False
            
        return True
    else:
        print("❌ 主應用文件不存在")
        return False

def test_analysis_reports():
    """測試分析報告"""
    print("\n🧪 測試分析報告")
    print("="*50)
    
    # 檢查分析報告文件
    report_files = glob.glob('backtest_analysis_report_*.md')
    summary_files = glob.glob('BACKTEST_SUMMARY.md')
    
    print(f"📄 找到分析報告: {len(report_files)} 個")
    for file in report_files:
        print(f"  - {file}")
    
    print(f"📋 找到總結報告: {len(summary_files)} 個")
    for file in summary_files:
        print(f"  - {file}")
    
    if report_files:
        latest_report = max(report_files, key=os.path.getctime)
        print(f"\n📖 最新報告: {latest_report}")
        
        # 檢查報告內容
        try:
            with open(latest_report, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if '布林通道策略回測分析報告' in content:
                print("✅ 報告標題正確")
            if '執行摘要' in content:
                print("✅ 包含執行摘要")
            if '表現最佳股票' in content:
                print("✅ 包含最佳股票清單")
            if '投資建議' in content:
                print("✅ 包含投資建議")
                
            return True
            
        except Exception as e:
            print(f"❌ 讀取報告失敗: {str(e)}")
            return False
    
    return len(report_files) > 0

def main():
    """主測試函數"""
    print("🎯 批量回測結果頁面功能測試")
    print("="*60)
    print(f"測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    tests = [
        ("回測結果載入", test_backtest_results_loading),
        ("Streamlit導入", test_streamlit_imports),
        ("應用結構", test_app_structure),
        ("分析報告", test_analysis_reports)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ 測試 {test_name} 發生錯誤: {str(e)}")
            results.append((test_name, False))
    
    # 總結
    print("\n" + "="*60)
    print("🎯 測試總結")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"{test_name:<20}: {status}")
    
    print(f"\n📊 測試結果: {passed}/{total} 通過")
    
    if passed == total:
        print("🎉 所有測試通過！批量回測結果頁面功能正常")
    else:
        print("⚠️ 部分測試失敗，請檢查相關功能")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 