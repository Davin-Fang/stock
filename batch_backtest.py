#!/usr/bin/env python3
"""
批量布林通道策略回測
對所有可用股票進行回測，篩選出報酬率10%以上的股票
"""

import pandas as pd
import numpy as np
import os
import glob
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

def calculate_bollinger_bands(df, window=20, num_std=2):
    """計算布林通道指標"""
    if df is None or len(df) < window:
        return df
    
    # 計算移動平均線
    df['MA'] = df['Close'].rolling(window=window).mean()
    
    # 計算標準差
    df['STD'] = df['Close'].rolling(window=window).std()
    
    # 計算布林帶
    df['Upper_Band'] = df['MA'] + (df['STD'] * num_std)
    df['Lower_Band'] = df['MA'] - (df['STD'] * num_std)
    
    return df

def bollinger_strategy_backtest(df, initial_capital=100000):
    """布林通道策略回測"""
    if df is None or len(df) < 50:
        return None
    
    # 添加布林通道指標
    df = calculate_bollinger_bands(df)
    
    # 去除NaN值
    df = df.dropna().copy()
    
    if len(df) < 10:
        return None
    
    # 初始化變量
    position = 0  # 0: 無持股, 1: 持股
    capital = initial_capital
    shares = 0
    trades = []
    
    for i in range(1, len(df)):
        current_price = df.iloc[i]['Close']
        prev_price = df.iloc[i-1]['Close']
        
        # 買入信號：價格觸及下軌且反彈
        if (position == 0 and 
            prev_price <= df.iloc[i-1]['Lower_Band'] and 
            current_price > df.iloc[i-1]['Lower_Band']):
            
            # 買入
            shares = capital // current_price
            if shares > 0:
                capital -= shares * current_price
                position = 1
                trades.append({
                    'Date': df.iloc[i]['Date'],
                    'Action': 'BUY',
                    'Price': current_price,
                    'Shares': shares,
                    'Capital': capital
                })
        
        # 賣出信號：價格觸及上軌
        elif (position == 1 and current_price >= df.iloc[i]['Upper_Band']):
            # 賣出
            capital += shares * current_price
            trades.append({
                'Date': df.iloc[i]['Date'],
                'Action': 'SELL',
                'Price': current_price,
                'Shares': shares,
                'Capital': capital
            })
            shares = 0
            position = 0
    
    # 如果最後還持有股票，以最後價格賣出
    if position == 1:
        final_price = df.iloc[-1]['Close']
        capital += shares * final_price
        trades.append({
            'Date': df.iloc[-1]['Date'],
            'Action': 'SELL (Final)',
            'Price': final_price,
            'Shares': shares,
            'Capital': capital
        })
    
    return {
        'final_capital': capital,
        'total_return': (capital - initial_capital) / initial_capital * 100,
        'trades': trades,
        'num_trades': len(trades)
    }

def load_stock_data(stock_code, period="1y"):
    """載入單支股票數據"""
    data_file = f'data/stock_prices/{stock_code}_price_data.csv'
    
    try:
        if not os.path.exists(data_file):
            return None
        
        # 讀取本地數據
        df = pd.read_csv(data_file)
        
        if df.empty:
            return None
        
        # 轉換日期格式
        df['Date'] = pd.to_datetime(df['Date'])
        
        # 根據期間篩選數據
        end_date = df['Date'].max()
        
        if period == "1y":
            start_date = end_date - timedelta(days=365)
        elif period == "2y":
            start_date = end_date - timedelta(days=730)
        elif period == "3y":
            start_date = end_date - timedelta(days=1095)
        else:
            start_date = end_date - timedelta(days=365)
        
        # 篩選期間內的數據
        filtered_df = df[df['Date'] >= start_date].copy()
        filtered_df = filtered_df.sort_values('Date').reset_index(drop=True)
        
        if len(filtered_df) < 50:
            return None
        
        return filtered_df
        
    except Exception as e:
        print(f"❌ 讀取股票 {stock_code} 數據失敗: {str(e)}")
        return None

def get_stock_name(stock_code):
    """從股票篩選數據獲取股票名稱"""
    try:
        # 嘗試載入股票篩選數據
        data_patterns = [
            'data/processed/fixed_real_stock_data_*.csv',
            'data/processed/hybrid_real_stock_data_*.csv',
            'data/processed/taiwan_all_stocks_complete_*.csv',
            'data/*stock_data_*.csv',
            '*stock_data_*.csv'
        ]
        
        latest_file = None
        for pattern in data_patterns:
            files = glob.glob(pattern)
            if files:
                latest_file = max(files, key=os.path.getctime)
                break
        
        if latest_file:
            df = pd.read_csv(latest_file)
            stock_info = df[df['stock_code'].str.contains(stock_code, na=False)]
            if not stock_info.empty:
                return stock_info.iloc[0]['name']
    except:
        pass
    
    return "未知"

def batch_backtest(period="1y", min_return=10.0, initial_capital=100000):
    """批量回測所有股票"""
    print("🚀 開始批量布林通道策略回測...")
    print(f"📊 回測期間: {period}")
    print(f"💰 初始資金: ${initial_capital:,}")
    print(f"🎯 最低報酬率門檻: {min_return}%")
    print("=" * 60)
    
    # 獲取所有股票數據文件
    data_files = glob.glob('data/stock_prices/*_price_data.csv')
    total_stocks = len(data_files)
    
    print(f"📈 找到 {total_stocks} 支股票數據")
    
    results = []
    successful_backtests = 0
    failed_backtests = 0
    
    for i, file_path in enumerate(data_files, 1):
        # 提取股票代碼
        stock_code = os.path.basename(file_path).replace('_price_data.csv', '')
        
        print(f"[{i:3d}/{total_stocks}] 回測 {stock_code}...", end=" ")
        
        # 載入股票數據
        stock_data = load_stock_data(stock_code, period)
        
        if stock_data is None:
            print("❌ 數據不足")
            failed_backtests += 1
            continue
        
        # 執行回測
        try:
            backtest_result = bollinger_strategy_backtest(stock_data, initial_capital)
            
            if backtest_result is None:
                print("❌ 回測失敗")
                failed_backtests += 1
                continue
            
            # 獲取股票名稱
            stock_name = get_stock_name(stock_code)
            
            # 記錄結果
            result = {
                'stock_code': stock_code,
                'stock_name': stock_name,
                'initial_capital': initial_capital,
                'final_capital': backtest_result['final_capital'],
                'total_return': backtest_result['total_return'],
                'num_trades': backtest_result['num_trades'],
                'data_points': len(stock_data),
                'start_date': stock_data['Date'].min().strftime('%Y-%m-%d'),
                'end_date': stock_data['Date'].max().strftime('%Y-%m-%d')
            }
            
            results.append(result)
            successful_backtests += 1
            
            print(f"✅ 報酬率: {backtest_result['total_return']:.2f}%")
            
        except Exception as e:
            print(f"❌ 錯誤: {str(e)}")
            failed_backtests += 1
    
    print("\n" + "=" * 60)
    print(f"📊 回測完成統計:")
    print(f"✅ 成功回測: {successful_backtests} 支")
    print(f"❌ 失敗回測: {failed_backtests} 支")
    print(f"📈 總計處理: {total_stocks} 支")
    
    if not results:
        print("❌ 沒有成功的回測結果")
        return None
    
    # 轉換為DataFrame
    results_df = pd.DataFrame(results)
    
    # 篩選報酬率大於門檻的股票
    profitable_stocks = results_df[results_df['total_return'] >= min_return].copy()
    profitable_stocks = profitable_stocks.sort_values('total_return', ascending=False)
    
    print(f"\n🎯 報酬率 >= {min_return}% 的股票:")
    print(f"📈 符合條件: {len(profitable_stocks)} 支")
    
    if len(profitable_stocks) > 0:
        print(f"🏆 最高報酬率: {profitable_stocks.iloc[0]['total_return']:.2f}%")
        print(f"📊 平均報酬率: {profitable_stocks['total_return'].mean():.2f}%")
    
    return results_df, profitable_stocks

def save_results(results_df, profitable_stocks, min_return=10.0):
    """保存回測結果"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # 保存完整結果
    full_results_file = f'backtest_results_full_{timestamp}.csv'
    results_df.to_csv(full_results_file, index=False, encoding='utf-8-sig')
    print(f"💾 完整結果已保存: {full_results_file}")
    
    # 保存符合條件的股票
    if len(profitable_stocks) > 0:
        profitable_file = f'backtest_results_profitable_{min_return}pct_{timestamp}.csv'
        profitable_stocks.to_csv(profitable_file, index=False, encoding='utf-8-sig')
        print(f"🎯 優質股票已保存: {profitable_file}")
        
        # 顯示前10名
        print(f"\n🏆 報酬率前10名:")
        print("-" * 80)
        for i, row in profitable_stocks.head(10).iterrows():
            print(f"{row['stock_code']:>6} | {row['stock_name']:<12} | "
                  f"報酬率: {row['total_return']:>7.2f}% | "
                  f"交易次數: {row['num_trades']:>3} | "
                  f"最終資金: ${row['final_capital']:>10,.0f}")

def main():
    """主函數"""
    print("🎯 台灣股票布林通道策略批量回測")
    print("=" * 60)
    
    # 回測參數設定
    period = "1y"  # 回測期間：1年
    min_return = 10.0  # 最低報酬率門檻：10%
    initial_capital = 100000  # 初始資金：10萬
    
    # 執行批量回測
    results = batch_backtest(period, min_return, initial_capital)
    
    if results is not None:
        results_df, profitable_stocks = results
        
        # 保存結果
        save_results(results_df, profitable_stocks, min_return)
        
        # 統計分析
        print(f"\n📊 整體統計分析:")
        print(f"總回測股票數: {len(results_df)}")
        print(f"平均報酬率: {results_df['total_return'].mean():.2f}%")
        print(f"報酬率標準差: {results_df['total_return'].std():.2f}%")
        print(f"最高報酬率: {results_df['total_return'].max():.2f}%")
        print(f"最低報酬率: {results_df['total_return'].min():.2f}%")
        print(f"正報酬股票數: {len(results_df[results_df['total_return'] > 0])}")
        print(f"負報酬股票數: {len(results_df[results_df['total_return'] < 0])}")
        
        # 報酬率分布
        print(f"\n📈 報酬率分布:")
        bins = [-100, -20, -10, 0, 10, 20, 50, 100, float('inf')]
        labels = ['<-20%', '-20~-10%', '-10~0%', '0~10%', '10~20%', '20~50%', '50~100%', '>100%']
        
        for i, label in enumerate(labels):
            if i < len(bins) - 1:
                count = len(results_df[(results_df['total_return'] >= bins[i]) & 
                                     (results_df['total_return'] < bins[i+1])])
                percentage = count / len(results_df) * 100
                print(f"{label:>10}: {count:>3} 支 ({percentage:>5.1f}%)")
    
    print("\n🎉 批量回測完成！")

if __name__ == "__main__":
    main() 