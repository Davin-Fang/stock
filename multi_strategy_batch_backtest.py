#!/usr/bin/env python3
"""
多策略批量回測工具
支持布林通道策略和突破策略的批量回測
"""

import pandas as pd
import numpy as np
import glob
import os
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# 從主應用導入策略函數
from stock_strategy_app import (
    calculate_bollinger_bands, 
    bollinger_strategy_backtest,
    calculate_breakout_indicators,
    breakout_strategy_backtest
)

def load_stock_price_data(stock_code):
    """載入單一股票的價格數據"""
    data_file = f'data/stock_prices/{stock_code}_price_data.csv'
    
    if not os.path.exists(data_file):
        return None
    
    try:
        df = pd.read_csv(data_file)
        if len(df) < 60:  # 突破策略需要至少60天數據
            return None
        
        df['Date'] = pd.to_datetime(df['Date'])
        df = df.sort_values('Date').reset_index(drop=True)
        return df
        
    except Exception as e:
        print(f"❌ 載入 {stock_code} 失敗: {str(e)}")
        return None

def get_available_stocks():
    """獲取所有可用的股票列表"""
    try:
        data_dir = 'data/stock_prices'
        if not os.path.exists(data_dir):
            return []
        
        files = glob.glob(os.path.join(data_dir, '*_price_data.csv'))
        available_stocks = []
        
        for file in files:
            stock_code = os.path.basename(file).replace('_price_data.csv', '')
            try:
                df = pd.read_csv(file)
                if len(df) >= 60:  # 確保有足夠數據
                    available_stocks.append(stock_code)
            except:
                continue
        
        return available_stocks
        
    except Exception as e:
        print(f"❌ 獲取股票列表失敗: {str(e)}")
        return []

def run_strategy_backtest(stock_code, strategy_name, **kwargs):
    """執行指定策略的回測"""
    try:
        # 載入股票數據
        price_data = load_stock_price_data(stock_code)
        if price_data is None:
            return None
        
        # 根據策略類型執行回測
        if strategy_name == "布林通道":
            result = bollinger_strategy_backtest(
                price_data.copy(),
                initial_capital=kwargs.get('initial_capital', 100000)
            )
        elif strategy_name == "突破策略":
            result = breakout_strategy_backtest(
                price_data.copy(),
                initial_capital=kwargs.get('initial_capital', 100000),
                stop_loss_pct=kwargs.get('stop_loss_pct', 6),
                take_profit_pct=kwargs.get('take_profit_pct', 15)
            )
        else:
            return None
        
        if result is None:
            return None
        
        # 計算額外統計信息
        trades = result['trades']
        if len(trades) > 1:
            # 計算勝率
            returns = [trade.get('Return', 0) for trade in trades if trade.get('Return') is not None]
            if returns:
                win_trades = len([r for r in returns if r > 0])
                total_trades = len(returns)
                win_rate = (win_trades / total_trades * 100) if total_trades > 0 else 0
                avg_return_per_trade = sum(returns) / len(returns) if returns else 0
                max_return = max(returns) if returns else 0
                min_return = min(returns) if returns else 0
            else:
                win_rate = 0
                avg_return_per_trade = 0
                max_return = 0
                min_return = 0
        else:
            win_rate = 0
            avg_return_per_trade = 0
            max_return = 0
            min_return = 0
        
        return {
            'stock_code': stock_code,
            'strategy': strategy_name,
            'total_return': result['total_return'],
            'final_capital': result['final_capital'],
            'num_trades': len(trades),
            'win_rate': win_rate,
            'avg_return_per_trade': avg_return_per_trade,
            'max_return': max_return,
            'min_return': min_return
        }
        
    except Exception as e:
        print(f"❌ {stock_code} 回測失敗: {str(e)}")
        return None

def batch_backtest_multiple_strategies():
    """多策略批量回測主函數"""
    print("🚀 多策略批量回測開始...")
    print("=" * 50)
    
    # 獲取可用股票
    available_stocks = get_available_stocks()
    
    if not available_stocks:
        print("❌ 沒有找到可用的股票數據")
        print("💡 請先執行 python twse_data_downloader.py 下載股票數據")
        return
    
    print(f"📊 找到 {len(available_stocks)} 支可用股票")
    
    # 策略配置
    strategies_config = {
        "布林通道": {
            "initial_capital": 100000
        },
        "突破策略": {
            "initial_capital": 100000,
            "stop_loss_pct": 6,
            "take_profit_pct": 15
        }
    }
    
    # 執行批量回測
    all_results = []
    
    for strategy_name, config in strategies_config.items():
        print(f"\n🎯 執行 {strategy_name} 批量回測...")
        strategy_results = []
        
        success_count = 0
        for i, stock_code in enumerate(available_stocks, 1):
            print(f"處理 {i}/{len(available_stocks)}: {stock_code}", end=" ")
            
            result = run_strategy_backtest(stock_code, strategy_name, **config)
            
            if result:
                strategy_results.append(result)
                success_count += 1
                print(f"✅ 報酬: {result['total_return']:.2f}%")
            else:
                print("❌ 失敗")
        
        print(f"\n📊 {strategy_name} 完成: {success_count}/{len(available_stocks)} 成功")
        all_results.extend(strategy_results)
    
    if not all_results:
        print("❌ 沒有成功的回測結果")
        return
    
    # 轉換為DataFrame
    results_df = pd.DataFrame(all_results)
    
    # 生成時間戳
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # 保存完整結果
    full_filename = f'multi_strategy_backtest_full_{timestamp}.csv'
    results_df.columns = [
        '股票代碼', '策略', '總報酬率(%)', '最終資金', '交易次數', 
        '勝率(%)', '平均單筆報酬(%)', '最大獲利(%)', '最大虧損(%)'
    ]
    results_df.to_csv(full_filename, index=False, encoding='utf-8-sig')
    print(f"💾 完整結果已保存: {full_filename}")
    
    # 篩選優質股票 (報酬率 >= 10%)
    profitable_df = results_df[results_df['總報酬率(%)'] >= 10.0]
    
    if len(profitable_df) > 0:
        profitable_filename = f'multi_strategy_backtest_profitable_{timestamp}.csv'
        profitable_df.to_csv(profitable_filename, index=False, encoding='utf-8-sig')
        print(f"🏆 優質股票結果已保存: {profitable_filename}")
        
        # 按策略分析
        print("\n📊 策略表現總結:")
        print("-" * 40)
        
        for strategy in results_df['策略'].unique():
            strategy_data = results_df[results_df['策略'] == strategy]
            profitable_count = len(strategy_data[strategy_data['總報酬率(%)'] >= 10])
            avg_return = strategy_data['總報酬率(%)'].mean()
            max_return = strategy_data['總報酬率(%)'].max()
            avg_win_rate = strategy_data['勝率(%)'].mean()
            
            print(f"\n🎯 {strategy}:")
            print(f"   總測試股票: {len(strategy_data)}")
            print(f"   優質股票: {profitable_count} ({profitable_count/len(strategy_data)*100:.1f}%)")
            print(f"   平均報酬: {avg_return:.2f}%")
            print(f"   最高報酬: {max_return:.2f}%")
            print(f"   平均勝率: {avg_win_rate:.1f}%")
        
        # Top 10 總覽
        print(f"\n🏆 各策略Top 5 表現:")
        print("-" * 40)
        
        for strategy in results_df['策略'].unique():
            strategy_data = results_df[results_df['策略'] == strategy]
            top5 = strategy_data.nlargest(5, '總報酬率(%)')
            
            print(f"\n📈 {strategy} Top 5:")
            for _, row in top5.iterrows():
                print(f"   {row['股票代碼']}: {row['總報酬率(%)']:.2f}% (勝率: {row['勝率(%)']:.1f}%)")
    
    else:
        print("⚠️ 沒有找到報酬率≥10%的股票")
    
    print(f"\n✅ 多策略批量回測完成!")
    print(f"📈 測試股票總數: {len(available_stocks)}")
    print(f"🎯 策略總數: {len(strategies_config)}")
    print(f"📊 總回測次數: {len(all_results)}")

if __name__ == "__main__":
    try:
        batch_backtest_multiple_strategies()
    except KeyboardInterrupt:
        print("\n⏹️ 回測被用戶中斷")
    except Exception as e:
        print(f"\n❌ 回測過程發生錯誤: {str(e)}") 