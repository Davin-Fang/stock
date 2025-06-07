#!/usr/bin/env python3
"""
演示數據生成器
為 Streamlit Cloud 部署提供示例數據
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta

def generate_sample_stock_data():
    """生成示例股票基础数据"""
    
    # 台灣知名股票列表
    stocks = [
        ('2330', '台積電', '半導體'),
        ('2454', '聯發科', '半導體'), 
        ('2317', '鴻海', '電子'),
        ('1301', '台塑', '化工'),
        ('2382', '廣達', '電子'),
        ('2303', '聯電', '半導體'),
        ('6505', '台達電', '電子'),
        ('2891', '中信金', '金融'),
        ('2308', '台達化', '化工'),
        ('2002', '中鋼', '鋼鐵'),
        ('1216', '統一', '食品'),
        ('1303', '南亞', '塑膠'),
        ('2881', '富邦金', '金融'),
        ('2886', '兆豐金', '金融'),
        ('2412', '中華電', '電信'),
        ('1326', '台化', '化工'),
        ('2207', '和泰車', '汽車'),
        ('2884', '玉山金', '金融'),
        ('2885', '元大金', '金融'),
        ('6669', '緯穎', '電子'),
    ]
    
    data = []
    np.random.seed(42)  # 確保數據一致性
    
    for code, name, sector in stocks:
        # 生成合理的財務指標
        base_roe = np.random.normal(15, 8)
        base_eps = np.random.normal(10, 8)
        revenue_growth = np.random.normal(8, 15)
        
        # 確保數據合理性
        roe = max(-20, min(50, base_roe))
        eps = max(-5, min(50, base_eps))
        revenue_growth = max(-30, min(80, revenue_growth))
        
        # 生成股價（基於EPS的合理倍數）
        pe_ratio = np.random.uniform(10, 25)
        current_price = max(10, eps * pe_ratio) if eps > 0 else np.random.uniform(20, 100)
        
        # 生成市值（億元）
        shares_outstanding = np.random.uniform(10, 50)  # 假設發行股數（億股）
        market_cap = current_price * shares_outstanding * 100000000  # 轉換為元
        
        data.append({
            'stock_code': code,
            'name': name,
            'sector': sector,
            'current_price': round(current_price, 1),
            'ROE': round(roe, 1),
            'EPS': round(eps, 2),
            '年營收成長率': round(revenue_growth, 1),
            'market_cap': int(market_cap),
            'PE_ratio': round(pe_ratio, 1),
            'shares_outstanding': round(shares_outstanding, 1)
        })
    
    return pd.DataFrame(data)

def generate_sample_price_data(stock_code, start_date=None, days=500):
    """生成示例股價數據"""
    
    if start_date is None:
        start_date = datetime.now() - timedelta(days=days)
    
    # 基於股票代碼生成種子，確保一致性
    seed = sum(ord(c) for c in stock_code)
    np.random.seed(seed)
    
    # 設定初始價格
    price_map = {
        '2330': 580, '2454': 920, '2317': 110, '1301': 95, '2382': 180,
        '2303': 48, '6505': 320, '2891': 23.5, '2308': 85, '2002': 28
    }
    
    initial_price = price_map.get(stock_code, 50)
    
    dates = []
    prices = []
    volumes = []
    
    current_price = initial_price
    current_date = start_date
    
    for i in range(days):
        # 跳過週末
        if current_date.weekday() < 5:  # 0-4 代表週一到週五
            
            # 生成價格變動（隨機遊走 + 趨勢）
            daily_return = np.random.normal(0.001, 0.025)  # 平均微漲，波動2.5%
            current_price *= (1 + daily_return)
            current_price = max(current_price, initial_price * 0.5)  # 設定下限
            
            # 生成 OHLC 數據
            high = current_price * (1 + abs(np.random.normal(0, 0.01)))
            low = current_price * (1 - abs(np.random.normal(0, 0.01)))
            open_price = current_price * (1 + np.random.normal(0, 0.005))
            
            # 確保 OHLC 邏輯正確
            high = max(high, open_price, current_price)
            low = min(low, open_price, current_price)
            
            # 生成成交量
            base_volume = 10000 if stock_code in ['2330', '2454'] else 5000
            volume = int(base_volume * np.random.lognormal(0, 0.5))
            
            dates.append(current_date)
            prices.append({
                'Date': current_date.strftime('%Y-%m-%d'),
                'Open': round(open_price, 2),
                'High': round(high, 2),
                'Low': round(low, 2),
                'Close': round(current_price, 2),
                'Volume': volume
            })
        
        current_date += timedelta(days=1)
    
    return pd.DataFrame(prices)

def create_demo_data_files():
    """創建演示數據文件"""
    
    # 確保目錄存在
    os.makedirs('data/processed', exist_ok=True)
    os.makedirs('data/stock_prices', exist_ok=True)
    
    # 生成股票基礎數據
    stock_data = generate_sample_stock_data()
    
    # 保存基礎數據
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    stock_data_file = f'data/processed/demo_stock_data_{timestamp}.csv'
    stock_data.to_csv(stock_data_file, index=False, encoding='utf-8-sig')
    
    print(f"✅ 生成股票基礎數據: {stock_data_file}")
    print(f"📊 股票數量: {len(stock_data)}")
    
    # 為前5支股票生成價格數據
    top_stocks = ['2330', '2454', '2317', '1301', '2382']
    
    for stock_code in top_stocks:
        price_data = generate_sample_price_data(stock_code)
        price_file = f'data/stock_prices/{stock_code}_price_data.csv'
        price_data.to_csv(price_file, index=False)
        print(f"✅ 生成 {stock_code} 價格數據: {len(price_data)} 筆記錄")
    
    print(f"\n🎉 演示數據生成完成！")
    print(f"📁 基礎數據文件: {stock_data_file}")
    print(f"📈 價格數據文件: data/stock_prices/")

if __name__ == "__main__":
    print("🚀 開始生成演示數據...")
    create_demo_data_files() 