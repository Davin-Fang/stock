import pandas as pd
import numpy as np
import os
from datetime import datetime

def create_sample_stock_data():
    """創建示例股票數據"""
    
    # 確保data/processed目錄存在
    os.makedirs('data/processed', exist_ok=True)
    
    # 台灣知名股票列表（示例）
    sample_stocks = [
        ('2330.TW', '台積電'),
        ('2317.TW', '鴻海'),
        ('2454.TW', '聯發科'),
        ('2891.TW', '中信金'),
        ('2882.TW', '國泰金'),
        ('2303.TW', '聯電'),
        ('2002.TW', '中鋼'),
        ('2881.TW', '富邦金'),
        ('2886.TW', '兆豐金'),
        ('2395.TW', '研華'),
        ('2412.TW', '中華電'),
        ('1301.TW', '台塑'),
        ('1303.TW', '南亞'),
        ('2207.TW', '和泰車'),
        ('2308.TW', '台達電'),
        ('2357.TW', '華碩'),
        ('2382.TW', '廣達'),
        ('2603.TW', '長榮'),
        ('3008.TW', '大立光'),
        ('6505.TW', '台塑化'),
        ('2327.TW', '國巨'),
        ('2379.TW', '瑞昱'),
        ('2344.TW', '華邦電'),
        ('2301.TW', '光寶科'),
        ('1216.TW', '統一'),
        ('2385.TW', '群光'),
        ('2409.TW', '友達'),
        ('2408.TW', '南亞科'),
        ('2884.TW', '玉山金'),
        ('2892.TW', '第一金'),
        ('3711.TW', '日月光投控'),
        ('2609.TW', '陽明'),
        ('2615.TW', '萬海'),
        ('2204.TW', '中華'),
        ('2323.TW', '中環'),
        ('2474.TW', '可成'),
        ('3034.TW', '聯詠'),
        ('2376.TW', '技嘉'),
        ('3045.TW', '台灣大'),
        ('4904.TW', '遠傳'),
        ('2912.TW', '統一超'),
        ('2105.TW', '正新'),
        ('1102.TW', '亞泥'),
        ('1101.TW', '台泥'),
        ('2105.TW', '正新'),
        ('6415.TW', '矽力-KY'),
        ('3443.TW', '創意'),
        ('2360.TW', '致茂'),
        ('3231.TW', '緯創'),
        ('6669.TW', '緯穎')
    ]
    
    # 生成隨機但合理的財務數據
    np.random.seed(42)  # 設定隨機種子以確保結果一致
    
    data = []
    for stock_code, name in sample_stocks:
        # 生成合理的財務指標
        roe = np.random.normal(15, 10)  # ROE 平均15%，標準差10%
        roe = max(-50, min(80, roe))  # 限制在合理範圍內
        
        eps = np.random.normal(3, 2)  # EPS 平均3，標準差2
        eps = max(-10, min(50, eps))  # 限制在合理範圍內
        
        # 年營收成長率（可能為負）
        annual_growth = np.random.normal(10, 25)
        annual_growth = max(-100, min(200, annual_growth))
        
        # 月營收成長率（通常比年成長率波動更大）
        monthly_growth = np.random.normal(8, 30)
        monthly_growth = max(-100, min(300, monthly_growth))
        
        data.append({
            'stock_code': stock_code,
            'name': name,
            'ROE': round(roe, 2),
            'EPS': round(eps, 2),
            '年營收成長率': round(annual_growth, 2),
            '月營收成長率': round(monthly_growth, 2)
        })
    
    # 創建DataFrame
    df = pd.DataFrame(data)
    
    # 保存到CSV文件
    filename = f'data/processed/stock_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    df.to_csv(filename, index=False, encoding='utf-8-sig')
    
    print(f"✅ 示例股票數據已生成: {filename}")
    print(f"📊 包含 {len(df)} 支股票的數據")
    print("\n前5筆數據預覽:")
    print(df.head())
    
    # 顯示一些統計信息
    print(f"\n📈 數據統計:")
    print(f"ROE 範圍: {df['ROE'].min():.2f}% ~ {df['ROE'].max():.2f}%")
    print(f"EPS 範圍: {df['EPS'].min():.2f} ~ {df['EPS'].max():.2f}")
    print(f"年營收成長率範圍: {df['年營收成長率'].min():.2f}% ~ {df['年營收成長率'].max():.2f}%")
    print(f"月營收成長率範圍: {df['月營收成長率'].min():.2f}% ~ {df['月營收成長率'].max():.2f}%")
    
    # 顯示符合高標準的股票數量
    high_quality = df[
        (df['ROE'] > 15) & 
        (df['EPS'] > 0) & 
        (df['年營收成長率'] > 20) & 
        (df['月營收成長率'] > 20)
    ]
    print(f"\n🎯 符合高標準的股票數量 (ROE>15%, EPS>0, 年成長>20%, 月成長>20%): {len(high_quality)}")
    
    return filename

if __name__ == "__main__":
    create_sample_stock_data() 