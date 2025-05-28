#!/usr/bin/env python3
"""
快速台灣股票數據生成器
生成高質量的示例數據，包含 ROE、EPS、年營收成長率、月營收成長率等關鍵指標
與股票分析工具完全兼容
"""

import pandas as pd
import numpy as np
from datetime import datetime
import os

def generate_taiwan_stock_data():
    """生成台灣股票數據"""
    
    # 台灣知名股票清單
    taiwan_stocks = [
        # 科技股 - 台積電供應鏈
        ('2330', '台積電'),
        ('2454', '聯發科'),
        ('3711', '日月光投控'),
        ('2303', '聯電'),
        ('3034', '聯詠'),
        ('6415', '矽力-KY'),
        ('3443', '創意'),
        ('2379', '瑞昱'),
        
        # 電子代工與製造
        ('2317', '鴻海'),
        ('2382', '廣達'),
        ('2357', '華碩'),
        ('2308', '台達電'),
        ('2327', '國巨'),
        ('3231', '緯創'),
        ('2324', '仁寶'),
        ('2376', '技嘉'),
        
        # 金融股
        ('2891', '中信金'),
        ('2882', '國泰金'),
        ('2881', '富邦金'),
        ('2886', '兆豐金'),
        ('2884', '玉山金'),
        ('2892', '第一金'),
        ('2885', '元大金'),
        ('2887', '台新金'),
        
        # 傳統產業
        ('2002', '中鋼'),
        ('1301', '台塑'),
        ('1303', '南亞'),
        ('6505', '台塑化'),
        ('1101', '台泥'),
        ('1216', '統一'),
        ('2105', '正新'),
        ('1326', '台化'),
        
        # 電信與公用事業
        ('2412', '中華電'),
        ('3045', '台灣大'),
        ('4904', '遠傳'),
        
        # 航運與交通
        ('2603', '長榮'),
        ('2609', '陽明'),
        ('2615', '萬海'),
        ('2207', '和泰車'),
        
        # 光電與精密
        ('3008', '大立光'),
        ('2474', '可成'),
        ('6176', '瑞儀'),
        ('3481', '群創'),
        
        # 生技醫療
        ('4968', '立積'),
        ('6446', '藥華藥'),
        
        # 其他重要股票
        ('2395', '研華'),
        ('2912', '統一超'),
        ('5880', '合庫金'),
        ('2633', '台灣高鐵')
    ]
    
    # 設定隨機種子以確保數據一致性
    np.random.seed(42)
    
    stock_data = []
    
    for i, (code, name) in enumerate(taiwan_stocks):
        # 根據不同類型股票設定不同的參數範圍
        if '金' in name:
            # 金融股特性
            roe_range = (8, 18)
            eps_range = (0.8, 2.5)
            annual_growth_range = (-5, 15)
            monthly_growth_range = (-10, 20)
            sector = 'Financial Services'
            industry = 'Banks' if '銀' in name else 'Insurance'
            
        elif code in ['2330', '2454', '3711', '2303', '3034']:
            # 半導體股特性
            roe_range = (15, 30)
            eps_range = (2, 8)
            annual_growth_range = (10, 50)
            monthly_growth_range = (5, 60)
            sector = 'Technology'
            industry = 'Semiconductors'
            
        elif code in ['2317', '2382', '2357']:
            # 電子代工股特性
            roe_range = (10, 25)
            eps_range = (1.5, 5)
            annual_growth_range = (5, 30)
            monthly_growth_range = (0, 40)
            sector = 'Technology'
            industry = 'Electronic Equipment'
            
        elif code in ['2412', '3045', '4904']:
            # 電信股特性
            roe_range = (8, 15)
            eps_range = (2, 4)
            annual_growth_range = (-2, 8)
            monthly_growth_range = (-5, 10)
            sector = 'Communication Services'
            industry = 'Telecom Services'
            
        elif code in ['2002', '1301', '1303']:
            # 傳統產業特性
            roe_range = (5, 20)
            eps_range = (0.5, 3)
            annual_growth_range = (-10, 25)
            monthly_growth_range = (-15, 30)
            sector = 'Basic Materials'
            industry = 'Steel' if code == '2002' else 'Chemicals'
            
        else:
            # 其他股票
            roe_range = (8, 22)
            eps_range = (1, 4)
            annual_growth_range = (0, 20)
            monthly_growth_range = (-5, 25)
            sector = 'Industrials'
            industry = 'Manufacturing'
        
        # 生成數據
        roe = round(np.random.uniform(*roe_range), 2)
        eps = round(np.random.uniform(*eps_range), 2)
        annual_growth = round(np.random.uniform(*annual_growth_range), 2)
        monthly_growth = round(np.random.uniform(*monthly_growth_range), 2)
        
        # 市值（根據股票規模）
        if code in ['2330', '2317', '2454']:  # 大型股
            market_cap = int(np.random.uniform(5e12, 15e12))
        elif '金' in name:  # 金融股
            market_cap = int(np.random.uniform(1e12, 8e12))
        else:  # 中型股
            market_cap = int(np.random.uniform(1e11, 5e12))
        
        stock_data.append({
            'stock_code': f"{code}.TW",
            'name': name,
            'ROE': roe,
            'EPS': eps,
            '年營收成長率': annual_growth,
            '月營收成長率': monthly_growth,
            'market_cap': market_cap,
            'sector': sector,
            'industry': industry
        })
    
    return pd.DataFrame(stock_data)

def create_sample_data_file():
    """創建示例數據文件"""
    print("🎯 生成台灣股票示例數據...")
    
    # 確保資料夾存在
    data_dir = 'data'
    processed_dir = os.path.join(data_dir, 'processed')
    os.makedirs(processed_dir, exist_ok=True)
    
    # 生成數據
    df = generate_taiwan_stock_data()
    
    # 數據統計
    print(f"📊 生成股票數量: {len(df)}")
    print(f"📈 ROE 範圍: {df['ROE'].min():.2f}% ~ {df['ROE'].max():.2f}%")
    print(f"💰 EPS 範圍: {df['EPS'].min():.2f} ~ {df['EPS'].max():.2f}")
    print(f"📊 年營收成長率範圍: {df['年營收成長率'].min():.2f}% ~ {df['年營收成長率'].max():.2f}%")
    
    # 產業分布
    print(f"\n🏭 產業分布:")
    sector_counts = df['sector'].value_counts()
    for sector, count in sector_counts.items():
        print(f"  {sector}: {count} 支")
    
    # 優質股票統計
    quality_stocks = df[
        (df['ROE'] > 15) & 
        (df['EPS'] > 2) & 
        (df['年營收成長率'] > 10)
    ]
    print(f"\n🏆 優質股票 (ROE>15%, EPS>2, 年成長>10%): {len(quality_stocks)} 支")
    
    if len(quality_stocks) > 0:
        print("前5名優質股票:")
        top5 = quality_stocks.nlargest(5, 'ROE')
        for _, row in top5.iterrows():
            print(f"  {row['stock_code']} {row['name']}: ROE={row['ROE']:.2f}%, EPS={row['EPS']:.2f}")
    
    # 保存文件
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = os.path.join(processed_dir, f'taiwan_stock_sample_{timestamp}.csv')
    df.to_csv(filename, index=False, encoding='utf-8-sig')
    
    print(f"\n💾 數據已保存至: {filename}")
    print(f"📝 文件大小: {os.path.getsize(filename) / 1024:.1f} KB")
    
    return filename

def validate_data_compatibility():
    """驗證數據與分析工具的兼容性"""
    print("\n🔧 驗證數據兼容性...")
    
    # 生成測試數據
    df = generate_taiwan_stock_data()
    
    # 檢查必要欄位
    required_columns = ['stock_code', 'name', 'ROE', 'EPS', '年營收成長率', '月營收成長率']
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        print(f"❌ 缺少欄位: {missing_columns}")
        return False
    else:
        print("✅ 所有必要欄位都存在")
    
    # 檢查數據類型
    for col in ['ROE', 'EPS', '年營收成長率', '月營收成長率']:
        if not pd.api.types.is_numeric_dtype(df[col]):
            print(f"❌ {col} 不是數字類型")
            return False
        else:
            print(f"✅ {col} 數據類型正確")
    
    # 檢查數據範圍
    if df['ROE'].min() < 0 or df['ROE'].max() > 100:
        print(f"⚠️ ROE 範圍可能不合理: {df['ROE'].min():.2f}% ~ {df['ROE'].max():.2f}%")
    
    print("✅ 數據兼容性驗證通過")
    return True

def main():
    """主函數"""
    print("🚀 台灣股票數據快速生成器")
    print("=" * 50)
    
    try:
        # 驗證兼容性
        if not validate_data_compatibility():
            print("❌ 數據兼容性驗證失敗")
            return
        
        # 生成數據文件
        filename = create_sample_data_file()
        
        print("\n" + "=" * 50)
        print("🎉 數據生成完成！")
        print(f"📁 數據文件: {filename}")
        print("💡 您現在可以使用以下命令來分析數據:")
        print("   python taiwan_stock_analyzer.py")
        print("   然後選擇剛生成的數據文件")
        print("=" * 50)
        
    except Exception as e:
        print(f"❌ 生成過程發生錯誤: {str(e)}")

if __name__ == "__main__":
    main() 