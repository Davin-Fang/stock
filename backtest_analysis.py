#!/usr/bin/env python3
"""
布林通道策略回測結果分析
生成詳細的分析報告和可視化圖表
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import glob
import os

# 設定中文字體
plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False

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
        
        # 前10名
        print(f"\n🥇 報酬率前10名:")
        print("-" * 80)
        for i, row in profitable_df.head(10).iterrows():
            print(f"{row['stock_code']:>6} | {row['stock_name']:<12} | "
                  f"報酬率: {row['total_return']:>7.2f}% | "
                  f"交易次數: {row['num_trades']:>3} | "
                  f"最終資金: ${row['final_capital']:>10,.0f}")
    
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

def create_visualizations(full_df, profitable_df):
    """創建可視化圖表"""
    print(f"\n📊 生成可視化圖表...")
    
    # 設定圖表樣式
    plt.style.use('seaborn-v0_8')
    fig = plt.figure(figsize=(20, 16))
    
    # 1. 報酬率分布直方圖
    plt.subplot(3, 3, 1)
    plt.hist(full_df['total_return'], bins=50, alpha=0.7, color='skyblue', edgecolor='black')
    plt.axvline(full_df['total_return'].mean(), color='red', linestyle='--', 
                label=f'平均值: {full_df["total_return"].mean():.2f}%')
    plt.axvline(0, color='green', linestyle='-', alpha=0.5, label='損益平衡點')
    plt.xlabel('報酬率 (%)')
    plt.ylabel('股票數量')
    plt.title('報酬率分布直方圖')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # 2. 報酬率箱型圖
    plt.subplot(3, 3, 2)
    box_data = [full_df['total_return']]
    if len(profitable_df) > 0:
        box_data.append(profitable_df['total_return'])
        labels = ['全部股票', '優質股票(≥10%)']
    else:
        labels = ['全部股票']
    
    plt.boxplot(box_data, labels=labels)
    plt.ylabel('報酬率 (%)')
    plt.title('報酬率箱型圖')
    plt.grid(True, alpha=0.3)
    
    # 3. 交易次數 vs 報酬率散點圖
    plt.subplot(3, 3, 3)
    colors = ['red' if x >= 10 else 'blue' for x in full_df['total_return']]
    plt.scatter(full_df['num_trades'], full_df['total_return'], 
                c=colors, alpha=0.6, s=30)
    plt.xlabel('交易次數')
    plt.ylabel('報酬率 (%)')
    plt.title('交易次數 vs 報酬率')
    plt.axhline(y=10, color='green', linestyle='--', alpha=0.7, label='10%門檻')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # 4. 勝率分析圓餅圖
    plt.subplot(3, 3, 4)
    positive_count = len(full_df[full_df['total_return'] > 0])
    negative_count = len(full_df[full_df['total_return'] <= 0])
    
    sizes = [positive_count, negative_count]
    labels = [f'正報酬\n{positive_count}支', f'負報酬\n{negative_count}支']
    colors = ['lightgreen', 'lightcoral']
    
    plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
    plt.title('勝率分析')
    
    # 5. 報酬率區間分布
    plt.subplot(3, 3, 5)
    bins = [-100, -50, -20, -10, 0, 10, 20, 50, 100, float('inf')]
    labels = ['<-50%', '-50~-20%', '-20~-10%', '-10~0%', '0~10%', '10~20%', '20~50%', '50~100%', '>100%']
    
    counts = []
    for i in range(len(bins)-1):
        count = len(full_df[(full_df['total_return'] >= bins[i]) & 
                           (full_df['total_return'] < bins[i+1])])
        counts.append(count)
    
    bars = plt.bar(labels, counts, color='lightblue', edgecolor='black')
    plt.xlabel('報酬率區間')
    plt.ylabel('股票數量')
    plt.title('報酬率區間分布')
    plt.xticks(rotation=45)
    
    # 在柱狀圖上顯示數值
    for bar, count in zip(bars, counts):
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, 
                str(count), ha='center', va='bottom')
    
    # 6. 交易次數分布
    plt.subplot(3, 3, 6)
    trade_counts = full_df['num_trades'].value_counts().sort_index()
    plt.bar(trade_counts.index, trade_counts.values, color='orange', alpha=0.7)
    plt.xlabel('交易次數')
    plt.ylabel('股票數量')
    plt.title('交易次數分布')
    plt.grid(True, alpha=0.3)
    
    # 7. 累積報酬率分布
    plt.subplot(3, 3, 7)
    sorted_returns = np.sort(full_df['total_return'])
    cumulative_prob = np.arange(1, len(sorted_returns) + 1) / len(sorted_returns)
    plt.plot(sorted_returns, cumulative_prob, linewidth=2)
    plt.axvline(x=0, color='red', linestyle='--', alpha=0.7, label='損益平衡點')
    plt.axvline(x=10, color='green', linestyle='--', alpha=0.7, label='10%門檻')
    plt.xlabel('報酬率 (%)')
    plt.ylabel('累積機率')
    plt.title('累積報酬率分布')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # 8. 優質股票報酬率分布（如果有的話）
    if len(profitable_df) > 0:
        plt.subplot(3, 3, 8)
        plt.hist(profitable_df['total_return'], bins=20, alpha=0.7, 
                color='lightgreen', edgecolor='black')
        plt.axvline(profitable_df['total_return'].mean(), color='red', linestyle='--',
                   label=f'平均值: {profitable_df["total_return"].mean():.2f}%')
        plt.xlabel('報酬率 (%)')
        plt.ylabel('股票數量')
        plt.title('優質股票報酬率分布 (≥10%)')
        plt.legend()
        plt.grid(True, alpha=0.3)
    
    # 9. 報酬率 vs 最終資金
    plt.subplot(3, 3, 9)
    colors = ['red' if x >= 10 else 'blue' for x in full_df['total_return']]
    plt.scatter(full_df['total_return'], full_df['final_capital'], 
                c=colors, alpha=0.6, s=30)
    plt.xlabel('報酬率 (%)')
    plt.ylabel('最終資金')
    plt.title('報酬率 vs 最終資金')
    plt.axvline(x=10, color='green', linestyle='--', alpha=0.7, label='10%門檻')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # 保存圖表
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    chart_filename = f'backtest_analysis_charts_{timestamp}.png'
    plt.savefig(chart_filename, dpi=300, bbox_inches='tight')
    print(f"📊 圖表已保存: {chart_filename}")
    
    plt.show()

def generate_detailed_report(full_df, profitable_df):
    """生成詳細的分析報告"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_filename = f'backtest_analysis_report_{timestamp}.md'
    
    with open(report_filename, 'w', encoding='utf-8') as f:
        f.write("# 🎯 布林通道策略回測分析報告\n\n")
        f.write(f"**生成時間**: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}\n\n")
        
        f.write("## 📊 執行摘要\n\n")
        f.write(f"- **回測股票數**: {len(full_df):,} 支\n")
        f.write(f"- **平均報酬率**: {full_df['total_return'].mean():.2f}%\n")
        f.write(f"- **勝率**: {len(full_df[full_df['total_return'] > 0]) / len(full_df) * 100:.1f}%\n")
        f.write(f"- **優質股票數** (≥10%): {len(profitable_df):,} 支\n")
        f.write(f"- **最高報酬率**: {full_df['total_return'].max():.2f}%\n\n")
        
        f.write("## 🏆 表現最佳股票 (前20名)\n\n")
        f.write("| 排名 | 股票代碼 | 股票名稱 | 報酬率 | 交易次數 | 最終資金 |\n")
        f.write("|------|----------|----------|--------|----------|----------|\n")
        
        if len(profitable_df) > 0:
            for i, row in profitable_df.head(20).iterrows():
                f.write(f"| {i+1:2d} | {row['stock_code']} | {row['stock_name']} | "
                       f"{row['total_return']:7.2f}% | {row['num_trades']:3d} | "
                       f"${row['final_capital']:10,.0f} |\n")
        
        f.write("\n## 📈 統計分析\n\n")
        f.write("### 報酬率統計\n")
        f.write(f"- **平均值**: {full_df['total_return'].mean():.2f}%\n")
        f.write(f"- **中位數**: {full_df['total_return'].median():.2f}%\n")
        f.write(f"- **標準差**: {full_df['total_return'].std():.2f}%\n")
        f.write(f"- **最大值**: {full_df['total_return'].max():.2f}%\n")
        f.write(f"- **最小值**: {full_df['total_return'].min():.2f}%\n\n")
        
        f.write("### 報酬率分布\n")
        bins = [-100, -50, -20, -10, 0, 10, 20, 50, 100, float('inf')]
        labels = ['<-50%', '-50~-20%', '-20~-10%', '-10~0%', '0~10%', '10~20%', '20~50%', '50~100%', '>100%']
        
        for i, label in enumerate(labels):
            if i < len(bins) - 1:
                count = len(full_df[(full_df['total_return'] >= bins[i]) & 
                                   (full_df['total_return'] < bins[i+1])])
                percentage = count / len(full_df) * 100
                f.write(f"- **{label}**: {count} 支 ({percentage:.1f}%)\n")
        
        f.write("\n## 🎯 策略評估\n\n")
        f.write("### 優點\n")
        if len(profitable_df) > 0:
            f.write(f"- 有 {len(profitable_df)} 支股票達到10%以上報酬率\n")
            f.write(f"- 最高報酬率達到 {full_df['total_return'].max():.2f}%\n")
        
        win_rate = len(full_df[full_df['total_return'] > 0]) / len(full_df) * 100
        if win_rate > 50:
            f.write(f"- 勝率達到 {win_rate:.1f}%，超過50%\n")
        
        f.write("\n### 風險提醒\n")
        f.write(f"- 最大虧損達到 {full_df['total_return'].min():.2f}%\n")
        f.write(f"- 報酬率標準差為 {full_df['total_return'].std():.2f}%，波動較大\n")
        f.write("- 過去績效不代表未來表現\n")
        f.write("- 實際交易需考慮手續費和滑價成本\n\n")
        
        f.write("## 📝 建議\n\n")
        f.write("1. **風險管理**: 建議設定停損點，控制單筆投資風險\n")
        f.write("2. **分散投資**: 不要將資金集中在單一股票\n")
        f.write("3. **參數優化**: 可嘗試調整布林通道參數以提升表現\n")
        f.write("4. **基本面分析**: 結合基本面分析選擇優質股票\n")
        f.write("5. **定期檢視**: 定期檢視策略表現並調整\n\n")
        
        f.write("---\n")
        f.write("*本報告僅供參考，投資有風險，請謹慎評估*\n")
    
    print(f"📄 詳細報告已保存: {report_filename}")

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
    
    # 生成可視化圖表
    create_visualizations(full_df, profitable_df)
    
    # 生成詳細報告
    generate_detailed_report(full_df, profitable_df)
    
    print("\n🎉 分析完成！")

if __name__ == "__main__":
    main() 