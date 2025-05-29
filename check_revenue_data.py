import pandas as pd
import numpy as np

# 載入數據
df = pd.read_csv('data/processed/hybrid_real_stock_data_20250529_013229.csv')

print("=== 營收成長率數據分析 ===")
print(f"總股票數: {len(df)}")
print()

print("年營收成長率統計:")
print(df['年營收成長率'].describe())
print()

print("月營收成長率統計:")
print(df['月營收成長率'].describe())
print()

print("=== 異常數據檢查 ===")
print(f"年營收成長率 > 100%: {(df['年營收成長率'] > 100).sum()} 筆")
print(f"年營收成長率 < -50%: {(df['年營收成長率'] < -50).sum()} 筆") 
print(f"月營收成長率 > 100%: {(df['月營收成長率'] > 100).sum()} 筆")
print(f"月營收成長率 < -50%: {(df['月營收成長率'] < -50).sum()} 筆")
print()

print("=== 數據範圍檢查 ===")
print(f"年營收成長率最小值: {df['年營收成長率'].min():.2f}%")
print(f"年營收成長率最大值: {df['年營收成長率'].max():.2f}%")
print(f"月營收成長率最小值: {df['月營收成長率'].min():.2f}%")
print(f"月營收成長率最大值: {df['月營收成長率'].max():.2f}%")
print()

print("=== 可疑數據樣本 ===")
# 找出極端值
extreme_annual = df[(df['年營收成長率'] > 50) | (df['年營收成長率'] < -30)]
extreme_monthly = df[(df['月營收成長率'] > 50) | (df['月營收成長率'] < -30)]

if len(extreme_annual) > 0:
    print("年營收成長率極端值 (>50% 或 <-30%):")
    print(extreme_annual[['stock_code', 'name', '年營收成長率']].head(10))
    print()

if len(extreme_monthly) > 0:
    print("月營收成長率極端值 (>50% 或 <-30%):")
    print(extreme_monthly[['stock_code', 'name', '月營收成長率']].head(10))
    print()

print("=== 數據來源檢查 ===")
if 'data_sources' in df.columns:
    print("數據來源分布:")
    print(df['data_sources'].value_counts())
else:
    print("無數據來源信息")

print("\n=== 建議修正 ===")
reasonable_count = len(df[(df['年營收成長率'] >= -30) & (df['年營收成長率'] <= 50) & 
                         (df['月營收成長率'] >= -30) & (df['月營收成長率'] <= 50)])
print(f"合理範圍內的數據: {reasonable_count}/{len(df)} ({reasonable_count/len(df)*100:.1f}%)")

if reasonable_count < len(df) * 0.8:
    print("⚠️ 建議重新檢查營收成長率的計算邏輯")
    print("⚠️ 可能需要修正數據源或計算方式") 