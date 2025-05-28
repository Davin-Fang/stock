#!/usr/bin/env python3
"""
台灣股票篩選分析工具演示腳本
"""

import pandas as pd
import os
import sys
from datetime import datetime

def demo_filtering():
    """演示篩選功能"""
    print("🎯 台灣股票篩選分析工具演示")
    print("=" * 50)
    
    # 載入數據
    try:
        import glob
        files = glob.glob('data/processed/stock_data_*.csv')
        if not files:
            print("❌ 找不到股票數據，請先運行 create_sample_data.py")
            return
        
        latest_file = max(files, key=os.path.getctime)
        df = pd.read_csv(latest_file)
        print(f"📊 載入數據: {os.path.basename(latest_file)}")
        print(f"📈 股票總數: {len(df)} 支")
        
        # 清理數據
        for col in ['ROE', 'EPS', '年營收成長率', '月營收成長率']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        df = df.dropna(subset=['ROE', 'EPS', '年營收成長率', '月營收成長率'])
        
        print("\n📋 數據概覽:")
        print(f"ROE 範圍: {df['ROE'].min():.2f}% ~ {df['ROE'].max():.2f}%")
        print(f"EPS 範圍: {df['EPS'].min():.2f} ~ {df['EPS'].max():.2f}")
        print(f"年營收成長率範圍: {df['年營收成長率'].min():.2f}% ~ {df['年營收成長率'].max():.2f}%")
        print(f"月營收成長率範圍: {df['月營收成長率'].min():.2f}% ~ {df['月營收成長率'].max():.2f}%")
        
        # 演示不同篩選策略
        strategies = [
            {
                "name": "🎯 積極成長型策略",
                "desc": "尋找高ROE、高成長的優質股票",
                "filters": {"ROE": 20, "EPS": 2, "年營收成長率": 30, "月營收成長率": 30}
            },
            {
                "name": "💎 價值投資策略", 
                "desc": "穩定獲利、合理成長的績優股",
                "filters": {"ROE": 15, "EPS": 1, "年營收成長率": 10, "月營收成長率": 5}
            },
            {
                "name": "🛡️ 保守投資策略",
                "desc": "低風險、穩定收益的安全股票",
                "filters": {"ROE": 10, "EPS": 0.5, "年營收成長率": 5, "月營收成長率": 0}
            },
            {
                "name": "🚀 高成長策略",
                "desc": "專注營收快速成長的潛力股",
                "filters": {"ROE": 5, "EPS": 0, "年營收成長率": 50, "月營收成長率": 40}
            }
        ]
        
        print("\n" + "=" * 70)
        print("🔍 不同投資策略篩選結果演示")
        print("=" * 70)
        
        for strategy in strategies:
            print(f"\n{strategy['name']}")
            print(f"📝 策略說明: {strategy['desc']}")
            
            filters = strategy['filters']
            print(f"🎯 篩選條件: ROE>{filters['ROE']}%, EPS>{filters['EPS']}, "
                  f"年成長>{filters['年營收成長率']}%, 月成長>{filters['月營收成長率']}%")
            
            # 執行篩選
            filtered_df = df[
                (df['ROE'] > filters['ROE']) &
                (df['EPS'] > filters['EPS']) &
                (df['年營收成長率'] > filters['年營收成長率']) &
                (df['月營收成長率'] > filters['月營收成長率'])
            ]
            
            if len(filtered_df) > 0:
                print(f"✅ 符合條件: {len(filtered_df)} 支股票")
                
                # 顯示平均指標
                avg_roe = filtered_df['ROE'].mean()
                avg_eps = filtered_df['EPS'].mean()
                avg_annual = filtered_df['年營收成長率'].mean()
                avg_monthly = filtered_df['月營收成長率'].mean()
                
                print(f"📊 平均指標: ROE={avg_roe:.2f}%, EPS={avg_eps:.2f}, "
                      f"年成長={avg_annual:.2f}%, 月成長={avg_monthly:.2f}%")
                
                # 顯示前3名股票
                top_stocks = filtered_df.nlargest(3, 'ROE')
                print("🏆 ROE前3名股票:")
                for idx, (_, stock) in enumerate(top_stocks.iterrows(), 1):
                    print(f"   {idx}. {stock['name']} ({stock['stock_code']}) - "
                          f"ROE: {stock['ROE']:.2f}%, EPS: {stock['EPS']:.2f}")
            else:
                print("❌ 沒有股票符合此策略條件")
        
        print(f"\n" + "=" * 70)
        print("🎉 演示完成！")
        print("\n💡 如何使用完整分析工具:")
        print("1. 執行: python start_analyzer.py")
        print("2. 或直接執行: streamlit run taiwan_stock_analyzer.py")
        print("3. 在瀏覽器中調整篩選條件並查看詳細結果")
        print("4. 可以下載篩選結果和查看視覺化圖表")
        
        return True
        
    except Exception as e:
        print(f"❌ 演示過程中發生錯誤: {str(e)}")
        return False

def show_sample_data():
    """顯示示例數據"""
    try:
        import glob
        files = glob.glob('data/processed/stock_data_*.csv')
        if files:
            latest_file = max(files, key=os.path.getctime)
            df = pd.read_csv(latest_file)
            
            print("\n📋 示例數據預覽（前10筆）:")
            print("-" * 80)
            print(df.head(10).to_string(index=False))
            print("-" * 80)
    except Exception as e:
        print(f"⚠️ 無法顯示示例數據: {e}")

def main():
    # 檢查是否有數據
    import glob
    files = glob.glob('data/processed/stock_data_*.csv')
    
    if not files:
        print("⚠️ 找不到股票數據，正在生成示例數據...")
        try:
            import subprocess
            subprocess.run([sys.executable, 'create_sample_data.py'], check=True)
        except:
            print("❌ 無法生成示例數據")
            return
    
    # 顯示示例數據
    show_sample_data()
    
    # 執行演示
    demo_filtering()

if __name__ == "__main__":
    main() 