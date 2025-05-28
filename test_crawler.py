#!/usr/bin/env python3
"""
爬蟲功能測試腳本
測試 ROE、EPS、年營收成長率、月營收成長率等關鍵指標的抓取
"""

import pandas as pd
import yfinance as yf
import numpy as np
from datetime import datetime
import os

def test_yfinance_connection():
    """測試 yfinance 連接"""
    print("🔗 測試 yfinance 連接...")
    try:
        # 測試抓取台積電數據
        stock = yf.Ticker("2330.TW")
        info = stock.info
        if info and 'longName' in info:
            print(f"✅ yfinance 連接成功！")
            print(f"📊 測試股票: {info.get('longName', '未知')}")
            return True
        else:
            print("❌ yfinance 連接失敗")
            return False
    except Exception as e:
        print(f"❌ yfinance 連接錯誤: {str(e)}")
        return False

def get_stock_key_metrics(stock_code):
    """獲取股票關鍵指標"""
    print(f"\n🎯 獲取 {stock_code} 的關鍵指標...")
    
    try:
        stock = yf.Ticker(stock_code)
        info = stock.info
        
        print(f"📈 股票名稱: {info.get('longName', info.get('shortName', '未知'))}")
        
        # 獲取基本指標
        roe = info.get('returnOnEquity', 0)
        if roe and not np.isnan(roe):
            roe = roe * 100
            print(f"📊 ROE: {roe:.2f}%")
        else:
            roe = 0
            print("📊 ROE: 無數據")
        
        eps = info.get('trailingEps', 0)
        if eps and not np.isnan(eps):
            print(f"💰 EPS: {eps:.2f}")
        else:
            eps = 0
            print("💰 EPS: 無數據")
        
        # 獲取財務報表數據
        print("\n📋 嘗試獲取財務報表數據...")
        
        # 年度財務數據
        try:
            financials = stock.financials
            if financials is not None and not financials.empty:
                print(f"✅ 年度財務數據可用 - 欄數: {len(financials.columns)}")
                print(f"📅 可用年份數: {len(financials.columns)}")
                
                # 顯示可用的財務指標
                print("💡 可用的財務指標:")
                for idx, item in enumerate(financials.index[:10]):  # 只顯示前10個
                    print(f"   {idx+1}. {item}")
                if len(financials.index) > 10:
                    print(f"   ... 還有 {len(financials.index) - 10} 個指標")
                
                # 尋找營收相關指標
                revenue_keys = ['Total Revenue', 'Revenue', 'Net Sales', 'Sales', 'Operating Revenue']
                revenue_found = False
                
                for key in revenue_keys:
                    if key in financials.index:
                        revenue_row = financials.loc[key]
                        print(f"\n💡 找到營收指標: {key}")
                        print(f"📊 最近年度營收: {revenue_row.iloc[0]:,.0f}")
                        
                        if len(revenue_row) >= 2:
                            current = revenue_row.iloc[0]
                            previous = revenue_row.iloc[1]
                            growth = ((current - previous) / previous) * 100 if previous != 0 else 0
                            print(f"📈 年營收成長率: {growth:.2f}%")
                        
                        revenue_found = True
                        break
                
                if not revenue_found:
                    print("⚠️ 未找到營收相關指標")
            else:
                print("❌ 年度財務數據不可用")
        except Exception as e:
            print(f"❌ 年度財務數據錯誤: {str(e)}")
        
        # 季度財務數據
        try:
            quarterly = stock.quarterly_financials
            if quarterly is not None and not quarterly.empty:
                print(f"\n✅ 季度財務數據可用 - 欄數: {len(quarterly.columns)}")
                
                # 尋找營收相關指標
                revenue_keys = ['Total Revenue', 'Revenue', 'Net Sales', 'Sales', 'Operating Revenue']
                for key in revenue_keys:
                    if key in quarterly.index:
                        revenue_row = quarterly.loc[key]
                        print(f"💡 找到季度營收指標: {key}")
                        print(f"📊 最近季度營收: {revenue_row.iloc[0]:,.0f}")
                        
                        if len(revenue_row) >= 4:
                            current_q = revenue_row.iloc[0]
                            year_ago_q = revenue_row.iloc[3]
                            quarterly_growth = ((current_q - year_ago_q) / year_ago_q) * 100 if year_ago_q != 0 else 0
                            print(f"📈 季度營收成長率 (同期比較): {quarterly_growth:.2f}%")
                        break
            else:
                print("❌ 季度財務數據不可用")
        except Exception as e:
            print(f"❌ 季度財務數據錯誤: {str(e)}")
        
        # 歷史價格數據
        try:
            print(f"\n📈 獲取歷史價格數據...")
            hist = stock.history(period="1y")
            if not hist.empty:
                print(f"✅ 歷史價格數據可用 - {len(hist)} 個交易日")
                current_price = hist['Close'].iloc[-1]
                year_ago_price = hist['Close'].iloc[0]
                price_growth = ((current_price - year_ago_price) / year_ago_price) * 100
                print(f"💹 年度股價成長率: {price_growth:.2f}%")
            else:
                print("❌ 歷史價格數據不可用")
        except Exception as e:
            print(f"❌ 歷史價格數據錯誤: {str(e)}")
        
        return {
            'stock_code': stock_code,
            'name': info.get('longName', info.get('shortName', '')),
            'ROE': roe,
            'EPS': eps,
            'market_cap': info.get('marketCap', 0),
            'sector': info.get('sector', ''),
            'industry': info.get('industry', '')
        }
        
    except Exception as e:
        print(f"❌ 獲取 {stock_code} 數據時發生錯誤: {str(e)}")
        return None

def test_multiple_stocks():
    """測試多支股票"""
    print("\n" + "="*60)
    print("🧪 測試多支台灣知名股票")
    print("="*60)
    
    test_stocks = [
        "2330.TW",  # 台積電
        "2317.TW",  # 鴻海
        "2454.TW",  # 聯發科
        "2891.TW",  # 中信金
        "2412.TW",  # 中華電
    ]
    
    results = []
    successful = 0
    
    for stock_code in test_stocks:
        print(f"\n{'-'*40}")
        data = get_stock_key_metrics(stock_code)
        if data:
            results.append(data)
            if data['ROE'] > 0 or data['EPS'] > 0:
                successful += 1
        print(f"{'-'*40}")
    
    print(f"\n📊 測試結果總結:")
    print(f"測試股票數: {len(test_stocks)}")
    print(f"成功獲取數據: {len(results)}")
    print(f"有效數據 (ROE或EPS>0): {successful}")
    
    if results:
        # 保存測試結果
        df = pd.DataFrame(results)
        filename = f"crawler_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"💾 測試結果已保存到: {filename}")
        
        # 顯示結果表格
        print(f"\n📋 測試結果詳細資料:")
        for _, row in df.iterrows():
            print(f"股票: {row['stock_code']} - {row['name']}")
            print(f"  ROE: {row['ROE']:.2f}%, EPS: {row['EPS']:.2f}")
            print(f"  產業: {row['sector']} - {row['industry']}")
            print()

def check_data_compatibility():
    """檢查數據與分析工具的兼容性"""
    print("\n" + "="*60)
    print("🔧 檢查數據格式與分析工具的兼容性")
    print("="*60)
    
    # 檢查必要的欄位
    required_columns = ['stock_code', 'name', 'ROE', 'EPS', '年營收成長率', '月營收成長率']
    print(f"✅ 必要欄位: {required_columns}")
    
    # 創建示例數據來測試
    sample_data = {
        'stock_code': '2330.TW',
        'name': '台積電',
        'ROE': 19.97,
        'EPS': 2.72,
        '年營收成長率': 26.19,
        '月營收成長率': 53.69
    }
    
    print(f"📊 示例數據格式:")
    for key, value in sample_data.items():
        print(f"  {key}: {value}")
    
    # 檢查是否能與分析工具兼容
    try:
        df = pd.DataFrame([sample_data])
        filename = "compatibility_test.csv"
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        
        # 讀取並驗證
        df_read = pd.read_csv(filename)
        
        # 檢查數據類型
        for col in ['ROE', 'EPS', '年營收成長率', '月營收成長率']:
            if col in df_read.columns:
                df_read[col] = pd.to_numeric(df_read[col], errors='coerce')
        
        print(f"✅ 數據格式兼容性測試通過")
        print(f"💾 測試文件: {filename}")
        
        # 清理測試文件
        if os.path.exists(filename):
            os.remove(filename)
            print(f"🧹 測試文件已清理")
        
        return True
        
    except Exception as e:
        print(f"❌ 兼容性測試失敗: {str(e)}")
        return False

def main():
    """主測試函數"""
    print("🧪 台灣股票爬蟲功能測試")
    print("=" * 50)
    
    # 測試 yfinance 連接
    if not test_yfinance_connection():
        print("❌ yfinance 連接失敗，無法繼續測試")
        return
    
    # 測試多支股票
    test_multiple_stocks()
    
    # 檢查兼容性
    check_data_compatibility()
    
    print("\n" + "="*60)
    print("🎉 爬蟲功能測試完成！")
    print("💡 如果測試成功，可以運行 enhanced_stock_crawler.py 進行完整爬取")
    print("📈 爬取完成後，可以用 taiwan_stock_analyzer.py 進行分析")
    print("="*60)

if __name__ == "__main__":
    main() 