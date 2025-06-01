#!/usr/bin/env python3
"""
布林通道策略回測結果簡化分析
生成詳細的文字分析報告
"""

import pandas as pd
import numpy as np
from datetime import datetime
import glob
import os

def load_latest_results():
    """載入最新的回測結果"""
    # 尋找最新的結果文件
    full_files = glob.glob('backtest_results_full_*.csv')
    profitable_files = glob.glob('backtest_results_profitable_*.csv')
    
    if not full_files:
        print("❌ 找不到回測結果文件")
        return None, None
    
    # 選擇最新的文件
    latest_full = max(full_files, key=os.path.getctime)
    latest_profitable = max(profitable_files, key=os.path.getctime) if profitable_files else None
    
    print(f"📊 載入完整結果: {latest_full}")
    if latest_profitable:
        print(f"🎯 載入優質股票: {latest_profitable}")
    
    full_df = pd.read_csv(latest_full)
    profitable_df = pd.read_csv(latest_profitable) if latest_profitable else pd.DataFrame()
    
    return full_df, profitable_df

def analyze_results(full_df, profitable_df):
    """分析回測結果"""
    print("\n" + "="*80)
    print("📊 布林通道策略回測結果分析報告")
    print("="*80)
    
    # 基本統計
    print(f"\n📈 基本統計:")
    print(f"總回測股票數: {len(full_df):,}")
    print(f"平均報酬率: {full_df['total_return'].mean():.2f}%")
    print(f"報酬率中位數: {full_df['total_return'].median():.2f}%")
    print(f"報酬率標準差: {full_df['total_return'].std():.2f}%")
    print(f"最高報酬率: {full_df['total_return'].max():.2f}%")
    print(f"最低報酬率: {full_df['total_return'].min():.2f}%")
    
    # 勝率分析
    positive_returns = len(full_df[full_df['total_return'] > 0])
    win_rate = positive_returns / len(full_df) * 100
    print(f"\n🎯 勝率分析:")
    print(f"正報酬股票數: {positive_returns:,}")
    print(f"負報酬股票數: {len(full_df) - positive_returns:,}")
    print(f"整體勝率: {win_rate:.1f}%")
    
    # 報酬率分布
    print(f"\n📊 報酬率分布:")
    bins = [-100, -50, -20, -10, 0, 10, 20, 50, 100, float('inf')]
    labels = ['<-50%', '-50~-20%', '-20~-10%', '-10~0%', '0~10%', '10~20%', '20~50%', '50~100%', '>100%']
    
    for i, label in enumerate(labels):
        if i < len(bins) - 1:
            count = len(full_df[(full_df['total_return'] >= bins[i]) & 
                               (full_df['total_return'] < bins[i+1])])
            percentage = count / len(full_df) * 100
            print(f"{label:>10}: {count:>3} 支 ({percentage:>5.1f}%)")
    
    # 優質股票分析
    if len(profitable_df) > 0:
        print(f"\n🏆 優質股票分析 (報酬率 >= 10%):")
        print(f"符合條件股票數: {len(profitable_df):,}")
        print(f"平均報酬率: {profitable_df['total_return'].mean():.2f}%")
        print(f"平均交易次數: {profitable_df['num_trades'].mean():.1f}")
        
        # 前20名
        print(f"\n🥇 報酬率前20名:")
        print("-" * 90)
        print(f"{'排名':>4} | {'代碼':>6} | {'名稱':<12} | {'報酬率':>8} | {'交易次數':>6} | {'最終資金':>12}")
        print("-" * 90)
        for i, row in profitable_df.head(20).iterrows():
            print(f"{i+1:>4} | {row['stock_code']:>6} | {row['stock_name']:<12} | "
                  f"{row['total_return']:>7.2f}% | {row['num_trades']:>6} | "
                  f"${row['final_capital']:>10,.0f}")
    
    # 交易次數分析
    print(f"\n🔄 交易次數分析:")
    print(f"平均交易次數: {full_df['num_trades'].mean():.1f}")
    print(f"交易次數中位數: {full_df['num_trades'].median():.0f}")
    print(f"最多交易次數: {full_df['num_trades'].max()}")
    print(f"最少交易次數: {full_df['num_trades'].min()}")
    
    # 交易次數分布
    trade_counts = full_df['num_trades'].value_counts().sort_index()
    print(f"\n交易次數分布:")
    for trades, count in trade_counts.head(10).items():
        percentage = count / len(full_df) * 100
        print(f"{trades:>2} 次交易: {count:>3} 支 ({percentage:>5.1f}%)")
    
    # 按行業分析（如果有行業資訊）
    print(f"\n📊 表現分析:")
    
    # 超高報酬率股票 (>50%)
    super_high = full_df[full_df['total_return'] > 50]
    if len(super_high) > 0:
        print(f"\n🚀 超高報酬率股票 (>50%):")
        for _, row in super_high.iterrows():
            print(f"  {row['stock_code']} {row['stock_name']}: {row['total_return']:.2f}%")
    
    # 高報酬率股票 (20-50%)
    high_return = full_df[(full_df['total_return'] >= 20) & (full_df['total_return'] <= 50)]
    if len(high_return) > 0:
        print(f"\n📈 高報酬率股票 (20-50%): {len(high_return)} 支")
        print("前10名:")
        for _, row in high_return.nlargest(10, 'total_return').iterrows():
            print(f"  {row['stock_code']} {row['stock_name']}: {row['total_return']:.2f}%")
    
    # 大幅虧損股票 (<-30%)
    big_loss = full_df[full_df['total_return'] < -30]
    if len(big_loss) > 0:
        print(f"\n⚠️  大幅虧損股票 (<-30%): {len(big_loss)} 支")
        print("虧損最大的5支:")
        for _, row in big_loss.nsmallest(5, 'total_return').iterrows():
            print(f"  {row['stock_code']} {row['stock_name']}: {row['total_return']:.2f}%")

def generate_detailed_report(full_df, profitable_df):
    """生成詳細的分析報告"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_filename = f'backtest_analysis_report_{timestamp}.md'
    
    with open(report_filename, 'w', encoding='utf-8') as f:
        f.write("# 🎯 布林通道策略回測分析報告\n\n")
        f.write(f"**生成時間**: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}\n\n")
        
        f.write("## 📊 執行摘要\n\n")
        f.write(f"本次回測對 **{len(full_df):,} 支台灣股票** 進行布林通道策略測試，回測期間為1年。\n\n")
        f.write("### 關鍵指標\n")
        f.write(f"- **回測股票數**: {len(full_df):,} 支\n")
        f.write(f"- **平均報酬率**: {full_df['total_return'].mean():.2f}%\n")
        f.write(f"- **勝率**: {len(full_df[full_df['total_return'] > 0]) / len(full_df) * 100:.1f}%\n")
        f.write(f"- **優質股票數** (≥10%): {len(profitable_df):,} 支 ({len(profitable_df)/len(full_df)*100:.1f}%)\n")
        f.write(f"- **最高報酬率**: {full_df['total_return'].max():.2f}%\n")
        f.write(f"- **最低報酬率**: {full_df['total_return'].min():.2f}%\n\n")
        
        f.write("## 🏆 表現最佳股票 (前30名)\n\n")
        f.write("| 排名 | 股票代碼 | 股票名稱 | 報酬率 | 交易次數 | 最終資金 |\n")
        f.write("|------|----------|----------|--------|----------|----------|\n")
        
        if len(profitable_df) > 0:
            for i, row in profitable_df.head(30).iterrows():
                f.write(f"| {i+1:2d} | {row['stock_code']} | {row['stock_name']} | "
                       f"{row['total_return']:7.2f}% | {row['num_trades']:3d} | "
                       f"${row['final_capital']:10,.0f} |\n")
        
        f.write("\n## 📈 統計分析\n\n")
        f.write("### 報酬率統計\n")
        f.write(f"- **平均值**: {full_df['total_return'].mean():.2f}%\n")
        f.write(f"- **中位數**: {full_df['total_return'].median():.2f}%\n")
        f.write(f"- **標準差**: {full_df['total_return'].std():.2f}%\n")
        f.write(f"- **最大值**: {full_df['total_return'].max():.2f}%\n")
        f.write(f"- **最小值**: {full_df['total_return'].min():.2f}%\n")
        f.write(f"- **25%分位數**: {full_df['total_return'].quantile(0.25):.2f}%\n")
        f.write(f"- **75%分位數**: {full_df['total_return'].quantile(0.75):.2f}%\n\n")
        
        f.write("### 報酬率分布\n")
        bins = [-100, -50, -20, -10, 0, 10, 20, 50, 100, float('inf')]
        labels = ['<-50%', '-50~-20%', '-20~-10%', '-10~0%', '0~10%', '10~20%', '20~50%', '50~100%', '>100%']
        
        for i, label in enumerate(labels):
            if i < len(bins) - 1:
                count = len(full_df[(full_df['total_return'] >= bins[i]) & 
                                   (full_df['total_return'] < bins[i+1])])
                percentage = count / len(full_df) * 100
                f.write(f"- **{label}**: {count} 支 ({percentage:.1f}%)\n")
        
        f.write("\n### 交易次數分析\n")
        f.write(f"- **平均交易次數**: {full_df['num_trades'].mean():.1f}\n")
        f.write(f"- **交易次數中位數**: {full_df['num_trades'].median():.0f}\n")
        f.write(f"- **最多交易次數**: {full_df['num_trades'].max()}\n")
        f.write(f"- **最少交易次數**: {full_df['num_trades'].min()}\n\n")
        
        # 超高報酬率股票
        super_high = full_df[full_df['total_return'] > 50]
        if len(super_high) > 0:
            f.write("## 🚀 超高報酬率股票 (>50%)\n\n")
            f.write("| 股票代碼 | 股票名稱 | 報酬率 | 交易次數 |\n")
            f.write("|----------|----------|--------|----------|\n")
            for _, row in super_high.iterrows():
                f.write(f"| {row['stock_code']} | {row['stock_name']} | {row['total_return']:.2f}% | {row['num_trades']} |\n")
            f.write("\n")
        
        f.write("## 🎯 策略評估\n\n")
        f.write("### 優點\n")
        if len(profitable_df) > 0:
            f.write(f"- 有 **{len(profitable_df)} 支股票** 達到10%以上報酬率，佔總數的 **{len(profitable_df)/len(full_df)*100:.1f}%**\n")
            f.write(f"- 最高報酬率達到 **{full_df['total_return'].max():.2f}%**，表現優異\n")
            f.write(f"- 優質股票平均報酬率為 **{profitable_df['total_return'].mean():.2f}%**\n")
        
        win_rate = len(full_df[full_df['total_return'] > 0]) / len(full_df) * 100
        if win_rate > 45:
            f.write(f"- 勝率達到 **{win_rate:.1f}%**，接近或超過50%\n")
        
        f.write("\n### 風險提醒\n")
        f.write(f"- 最大虧損達到 **{full_df['total_return'].min():.2f}%**，風險較高\n")
        f.write(f"- 報酬率標準差為 **{full_df['total_return'].std():.2f}%**，波動較大\n")
        
        big_loss_count = len(full_df[full_df['total_return'] < -20])
        f.write(f"- 有 **{big_loss_count} 支股票** 虧損超過20%，需注意風險控制\n")
        f.write("- 過去績效不代表未來表現\n")
        f.write("- 實際交易需考慮手續費和滑價成本\n\n")
        
        f.write("## 📝 投資建議\n\n")
        f.write("### 選股建議\n")
        if len(profitable_df) > 0:
            f.write("基於回測結果，以下股票在布林通道策略下表現較佳：\n\n")
            for i, row in profitable_df.head(10).iterrows():
                f.write(f"- **{row['stock_code']} {row['stock_name']}**: 報酬率 {row['total_return']:.2f}%\n")
        
        f.write("\n### 風險管理建議\n")
        f.write("1. **設定停損點**: 建議設定15-20%的停損點\n")
        f.write("2. **分散投資**: 不要將資金集中在單一股票\n")
        f.write("3. **資金管理**: 單筆投資不超過總資金的5-10%\n")
        f.write("4. **定期檢視**: 每月檢視策略表現並調整\n\n")
        
        f.write("### 策略優化建議\n")
        f.write("1. **參數調整**: 可嘗試不同的布林通道參數組合\n")
        f.write("2. **基本面篩選**: 結合財務指標篩選優質股票\n")
        f.write("3. **市場環境**: 考慮不同市場環境下的策略適用性\n")
        f.write("4. **交易成本**: 將手續費納入回測計算\n\n")
        
        f.write("---\n")
        f.write("*本報告僅供參考，投資有風險，請謹慎評估*\n")
    
    print(f"📄 詳細報告已保存: {report_filename}")
    return report_filename

def main():
    """主函數"""
    print("📊 布林通道策略回測結果分析")
    print("="*50)
    
    # 載入結果
    full_df, profitable_df = load_latest_results()
    
    if full_df is None:
        print("❌ 無法載入回測結果")
        return
    
    # 分析結果
    analyze_results(full_df, profitable_df)
    
    # 生成詳細報告
    report_file = generate_detailed_report(full_df, profitable_df)
    
    print(f"\n🎉 分析完成！")
    print(f"📄 詳細報告: {report_file}")
    print(f"📊 優質股票數量: {len(profitable_df)} 支")
    if len(profitable_df) > 0:
        print(f"🏆 最佳表現: {profitable_df.iloc[0]['stock_code']} {profitable_df.iloc[0]['stock_name']} ({profitable_df.iloc[0]['total_return']:.2f}%)")

if __name__ == "__main__":
    main() 