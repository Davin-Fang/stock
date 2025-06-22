#!/usr/bin/env python3
"""
台灣股票分析平台 - 多頁面版本
包含：
1. 股票篩選工具
2. 個股策略回測
3. 投資組合分析
"""

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import glob
import os
import warnings
warnings.filterwarnings('ignore')

# 設定頁面配置
st.set_page_config(
    page_title="台灣股票分析平台",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 自定義CSS樣式
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        color: #1f77b4;
        margin-bottom: 2rem;
        background: linear-gradient(90deg, #1f77b4, #ff7f0e, #2ca02c);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    
    .page-header {
        font-size: 2rem;
        font-weight: bold;
        color: #2c3e50;
        margin-bottom: 1.5rem;
        padding: 15px;
        background: linear-gradient(135deg, #f8f9fa, #e9ecef);
        border-radius: 15px;
        border-left: 5px solid #1f77b4;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    .metric-card {
        background: linear-gradient(135deg, #ffffff, #f8f9fa);
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 6px 12px rgba(0,0,0,0.1);
        margin: 1rem 0;
        border-left: 4px solid #1f77b4;
        transition: transform 0.2s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 16px rgba(0,0,0,0.15);
    }
    
    .strategy-result {
        background: linear-gradient(135deg, #e3f2fd, #f0f8ff);
        padding: 1.5rem;
        border-radius: 12px;
        border: 2px solid #1f77b4;
        margin: 1rem 0;
        box-shadow: 0 4px 8px rgba(31,119,180,0.1);
    }
    
    .warning-box {
        background: linear-gradient(135deg, #fff3cd, #ffeaa7);
        border: 1px solid #ffeeba;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .success-box {
        background: linear-gradient(135deg, #d4edda, #a8e6cf);
        border: 1px solid #c3e6cb;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .info-box {
        background: linear-gradient(135deg, #cce7ff, #b3d9ff);
        border: 1px solid #b8daff;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    /* Sidebar styling */
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #f8f9fa, #e9ecef);
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #1f77b4, #2e86ab);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: bold;
        transition: all 0.3s ease;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #2e86ab, #1f77b4);
        transform: translateY(-1px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    /* Radio button styling */
    .stRadio > label {
        background: linear-gradient(135deg, #f8f9fa, #ffffff);
        padding: 0.5rem;
        border-radius: 8px;
        margin: 0.2rem 0;
        border: 1px solid #dee2e6;
    }
    
    /* Selectbox styling */
    .stSelectbox > label {
        color: #2c3e50;
        font-weight: 600;
    }
    
    /* Metric styling */
    [data-testid="metric-container"] {
        background: linear-gradient(135deg, #ffffff, #f8f9fa);
        border: 1px solid #e9ecef;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    /* DataFrame styling */
    .dataframe {
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# 載入股票數據
@st.cache_data
def load_stock_data():
    """載入股票篩選數據"""
    data_patterns = [
        'data/processed/hybrid_real_stock_data_*.csv',
        'data/processed/fixed_real_stock_data_*.csv',
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
        try:
            df = pd.read_csv(latest_file)
            # 檢查數據質量，如果股票數量少於100支，使用示例數據
            if len(df) < 100:
                st.sidebar.warning(f"⚠️ 數據文件 {os.path.basename(latest_file)} 只有 {len(df)} 支股票，使用示例數據")
                return generate_demo_stock_data()
            st.sidebar.success(f"✅ 載入數據文件: {os.path.basename(latest_file)}")
            st.sidebar.info(f"📊 股票數量: {len(df)}")
            return df
        except Exception as e:
            st.sidebar.error(f"❌ 讀取數據失敗: {str(e)}")
            return generate_demo_stock_data()
    else:
        st.sidebar.warning("⚠️ 找不到本地數據文件，使用示例數據")
        return generate_demo_stock_data()

# 生成示例股票數據
@st.cache_data
def generate_demo_stock_data():
    """生成完整的示例股票數據供雲端使用"""
    demo_stocks = [
        # 大型權值股
        {'股票代號': '2330', '股票名稱': '台積電', 'ROE(%)': 25.5, 'EPS(元)': 22.0, '年營收成長率(%)': 18.5, '月營收成長率(%)': 12.3, '市值(億)': 15000, '產業': '半導體'},
        {'股票代號': '2317', '股票名稱': '鴻海', 'ROE(%)': 12.8, 'EPS(元)': 8.5, '年營收成長率(%)': 8.2, '月營收成長率(%)': 5.1, '市值(億)': 2500, '產業': '電子製造'},
        {'股票代號': '2454', '股票名稱': '聯發科', 'ROE(%)': 28.2, 'EPS(元)': 45.6, '年營收成長率(%)': 22.1, '月營收成長率(%)': 15.8, '市值(億)': 8500, '產業': '半導體'},
        {'股票代號': '1301', '股票名稱': '台塑', 'ROE(%)': 15.3, 'EPS(元)': 6.2, '年營收成長率(%)': 12.4, '月營收成長率(%)': 8.7, '市值(億)': 1800, '產業': '石化'},
        {'股票代號': '2382', '股票名稱': '廣達', 'ROE(%)': 18.7, 'EPS(元)': 12.3, '年營收成長率(%)': 25.6, '月營收成長率(%)': 18.9, '市值(億)': 3200, '產業': '電腦'},
        
        # 金融股
        {'股票代號': '2881', '股票名稱': '富邦金', 'ROE(%)': 11.2, 'EPS(元)': 4.8, '年營收成長率(%)': 6.5, '月營收成長率(%)': 3.2, '市值(億)': 2100, '產業': '金融'},
        {'股票代號': '2882', '股票名稱': '國泰金', 'ROE(%)': 10.8, 'EPS(元)': 4.2, '年營收成長率(%)': 5.8, '月營收成長率(%)': 2.9, '市值(億)': 1950, '產業': '金融'},
        {'股票代號': '2884', '股票名稱': '玉山金', 'ROE(%)': 9.5, 'EPS(元)': 1.8, '年營收成長率(%)': 4.2, '月營收成長率(%)': 1.5, '市值(億)': 1200, '產業': '金融'},
        {'股票代號': '2891', '股票名稱': '中信金', 'ROE(%)': 8.9, 'EPS(元)': 1.5, '年營收成長率(%)': 3.8, '月營收成長率(%)': 1.2, '市值(億)': 1100, '產業': '金融'},
        {'股票代號': '2892', '股票名稱': '第一金', 'ROE(%)': 7.2, 'EPS(元)': 1.2, '年營收成長率(%)': 2.5, '月營收成長率(%)': 0.8, '市值(億)': 850, '產業': '金融'},
        
        # 傳統產業
        {'股票代號': '1216', '股票名稱': '統一', 'ROE(%)': 13.5, 'EPS(元)': 3.8, '年營收成長率(%)': 7.2, '月營收成長率(%)': 4.1, '市值(億)': 1650, '產業': '食品'},
        {'股票代號': '1326', '股票名稱': '台化', 'ROE(%)': 16.2, 'EPS(元)': 5.5, '年營收成長率(%)': 10.8, '月營收成長率(%)': 6.9, '市值(億)': 1400, '產業': '化工'},
        {'股票代號': '2002', '股票名稱': '中鋼', 'ROE(%)': 8.8, 'EPS(元)': 2.1, '年營收成長率(%)': 5.5, '月營收成長率(%)': 2.8, '市值(億)': 1300, '產業': '鋼鐵'},
        {'股票代號': '2303', '股票名稱': '聯電', 'ROE(%)': 22.1, 'EPS(元)': 3.2, '年營收成長率(%)': 15.8, '月營收成長率(%)': 11.2, '市值(億)': 2800, '產業': '半導體'},
        {'股票代號': '2308', '股票名稱': '台達電', 'ROE(%)': 19.8, 'EPS(元)': 15.6, '年營收成長率(%)': 18.9, '月營收成長率(%)': 13.5, '市值(億)': 4500, '產業': '電子'},
        
        # 生技醫療
        {'股票代號': '4904', '股票名稱': '遠傳', 'ROE(%)': 14.2, 'EPS(元)': 4.5, '年營收成長率(%)': 8.8, '月營收成長率(%)': 5.2, '市值(億)': 1800, '產業': '電信'},
        {'股票代號': '6505', '股票名稱': '台塑化', 'ROE(%)': 17.5, 'EPS(元)': 7.8, '年營收成長率(%)': 14.2, '月營收成長率(%)': 9.1, '市值(億)': 2200, '產業': '石化'},
        {'股票代號': '3008', '股票名稱': '大立光', 'ROE(%)': 35.2, 'EPS(元)': 125.8, '年營收成長率(%)': 28.5, '月營收成長率(%)': 22.1, '市值(億)': 6800, '產業': '光學'},
        {'股票代號': '2412', '股票名稱': '中華電', 'ROE(%)': 12.8, 'EPS(元)': 5.2, '年營收成長率(%)': 3.5, '月營收成長率(%)': 1.8, '市值(億)': 3500, '產業': '電信'},
        {'股票代號': '2409', '股票名稱': '友達', 'ROE(%)': 8.5, 'EPS(元)': 1.8, '年營收成長率(%)': 6.2, '月營收成長率(%)': 3.5, '市值(億)': 850, '產業': '面板'},
        
        # 高成長股
        {'股票代號': '2379', '股票名稱': '瑞昱', 'ROE(%)': 32.5, 'EPS(元)': 28.5, '年營收成長率(%)': 35.2, '月營收成長率(%)': 28.8, '市值(億)': 3800, '產業': '半導體'},
        {'股票代號': '3711', '股票名稱': '日月光投控', 'ROE(%)': 16.8, 'EPS(元)': 4.2, '年營收成長率(%)': 12.5, '月營收成長率(%)': 8.9, '市值(億)': 2600, '產業': '半導體'},
        {'股票代號': '2357', '股票名稱': '華碩', 'ROE(%)': 18.5, 'EPS(元)': 25.8, '年營收成長率(%)': 15.2, '月營收成長率(%)': 11.8, '市值(億)': 2900, '產業': '電腦'},
        {'股票代號': '2376', '股票名稱': '技嘉', 'ROE(%)': 22.8, 'EPS(元)': 12.5, '年營收成長率(%)': 28.5, '月營收成長率(%)': 21.2, '市值(億)': 1500, '產業': '電腦'},
        {'股票代號': '6415', '股票名稱': '矽力-KY', 'ROE(%)': 28.5, 'EPS(元)': 45.2, '年營收成長率(%)': 32.8, '月營收成長率(%)': 25.5, '市值(億)': 4200, '產業': '半導體'},
        
        # 中小型成長股
        {'股票代號': '2474', '股票名稱': '可成', 'ROE(%)': 15.2, 'EPS(元)': 8.5, '年營收成長率(%)': 18.8, '月營收成長率(%)': 12.5, '市值(億)': 1200, '產業': '金屬'},
        {'股票代號': '3037', '股票名稱': '欣興', 'ROE(%)': 25.8, 'EPS(元)': 15.2, '年營收成長率(%)': 22.5, '月營收成長率(%)': 18.2, '市值(億)': 2100, '產業': '電子'},
        {'股票代號': '2408', '股票名稱': '南亞科', 'ROE(%)': 28.2, 'EPS(元)': 18.5, '年營收成長率(%)': 45.2, '月營收成長率(%)': 35.8, '市值(億)': 2800, '產業': '半導體'},
        {'股票代號': '3443', '股票名稱': '創意', 'ROE(%)': 35.8, 'EPS(元)': 52.5, '年營收成長率(%)': 38.5, '月營收成長率(%)': 32.1, '市值(億)': 3500, '產業': '半導體'},
        {'股票代號': '2609', '股票名稱': '陽明', 'ROE(%)': 45.2, 'EPS(元)': 35.8, '年營收成長率(%)': 85.2, '月營收成長率(%)': 65.8, '市值(億)': 3200, '產業': '航運'},
        
        # 穩健收益股
        {'股票代號': '1102', '股票名稱': '亞泥', 'ROE(%)': 12.5, 'EPS(元)': 3.2, '年營收成長率(%)': 8.5, '月營收成長率(%)': 5.2, '市值(億)': 950, '產業': '水泥'},
        {'股票代號': '1303', '股票名稱': '南亞', 'ROE(%)': 14.8, 'EPS(元)': 4.5, '年營收成長率(%)': 11.2, '月營收成長率(%)': 7.8, '市值(億)': 1650, '產業': '塑膠'},
        {'股票代號': '2105', '股票名稱': '正新', 'ROE(%)': 16.2, 'EPS(元)': 5.8, '年營收成長率(%)': 12.8, '月營收成長率(%)': 9.2, '市值(億)': 1400, '產業': '橡膠'},
        {'股票代號': '2207', '股票名稱': '和泰車', 'ROE(%)': 22.5, 'EPS(元)': 18.2, '年營收成長率(%)': 15.8, '月營收成長率(%)': 12.1, '市值(億)': 2800, '產業': '汽車'},
        {'股票代號': '2227', '股票名稱': '裕日車', 'ROE(%)': 18.8, 'EPS(元)': 12.5, '年營收成長率(%)': 18.2, '月營收成長率(%)': 14.5, '市值(億)': 1800, '產業': '汽車'},
        
        # 新興產業
        {'股票代號': '6669', '股票名稱': '緯穎', 'ROE(%)': 28.5, 'EPS(元)': 35.2, '年營收成長率(%)': 42.8, '月營收成長率(%)': 35.5, '市值(億)': 4500, '產業': '伺服器'},
        {'股票代號': '3034', '股票名稱': '聯詠', 'ROE(%)': 32.8, 'EPS(元)': 42.5, '年營收成長率(%)': 38.2, '月營收成長率(%)': 31.8, '市值(億)': 5200, '產業': '半導體'},
        {'股票代號': '2618', '股票名稱': '長榮航', 'ROE(%)': 25.8, 'EPS(元)': 22.5, '年營收成長率(%)': 35.8, '月營收成長率(%)': 28.2, '市值(億)': 2600, '產業': '航空'},
        {'股票代號': '2615', '股票名稱': '萬海', 'ROE(%)': 52.8, 'EPS(元)': 48.5, '年營收成長率(%)': 125.8, '月營收成長率(%)': 85.2, '市值(億)': 4800, '產業': '航運'},
        {'股票代號': '4968', '股票名稱': '立積', 'ROE(%)': 35.2, 'EPS(元)': 28.5, '年營收成長率(%)': 45.8, '月營收成長率(%)': 38.2, '市值(億)': 2200, '產業': '半導體'},
        
        # 特殊題材股
        {'股票代號': '2301', '股票名稱': '光寶科', 'ROE(%)': 15.8, 'EPS(元)': 3.2, '年營收成長率(%)': 12.5, '月營收成長率(%)': 8.8, '市值(億)': 1200, '產業': '光電'},
        {'股票代號': '2395', '股票名稱': '研華', 'ROE(%)': 22.5, 'EPS(元)': 15.8, '年營收成長率(%)': 18.2, '月營收成長率(%)': 14.5, '市值(億)': 3500, '產業': '工控'},
        {'股票代號': '3481', '股票名稱': '群創', 'ROE(%)': 8.2, 'EPS(元)': 1.5, '年營收成長率(%)': 5.8, '月營收成長率(%)': 3.2, '市值(億)': 850, '產業': '面板'},
        {'股票代號': '2356', '股票名稱': '英業達', 'ROE(%)': 12.8, 'EPS(元)': 2.8, '年營收成長率(%)': 8.5, '月營收成長率(%)': 5.2, '市值(億)': 950, '產業': '電腦'},
        {'股票代號': '2324', '股票名稱': '仁寶', 'ROE(%)': 14.2, 'EPS(元)': 1.8, '年營收成長率(%)': 6.5, '月營收成長率(%)': 4.2, '市值(億)': 750, '產業': '電腦'},
    ]
    
    df = pd.DataFrame(demo_stocks)
    
    # 添加一些額外的計算欄位
    df['P/E比'] = df['市值(億)'] * 100 / (df['EPS(元)'] * 1000000)  # 簡化計算
    df['股價淨值比'] = df['ROE(%)'] / 100 * 15  # 簡化計算
    df['殖利率(%)'] = np.random.uniform(1.5, 6.5, len(df))  # 隨機生成合理範圍的殖利率
    
    st.sidebar.success(f"✅ 載入示例數據")
    st.sidebar.info(f"📊 股票數量: {len(df)}")
    st.sidebar.warning("⚠️ 這是示例數據，非即時市場數據")
    
    return df

# 生成示例價格數據
@st.cache_data
def generate_demo_price_data(stock_code, period="1y"):
    """為雲端版本生成示例價格數據"""
    
    # 計算日期範圍
    end_date = datetime.now()
    if period == "1y":
        start_date = end_date - timedelta(days=365)
        days = 365
    elif period == "2y":
        start_date = end_date - timedelta(days=730)
        days = 730
    elif period == "3y":
        start_date = end_date - timedelta(days=1095)
        days = 1095
    elif period == "5y":
        start_date = end_date - timedelta(days=1825)
        days = 1825
    else:
        start_date = end_date - timedelta(days=365)
        days = 365
    
    # 生成日期序列（只包含工作日）
    dates = pd.bdate_range(start=start_date, end=end_date)
    
    # 根據股票代碼設定不同的基礎價格和波動性
    stock_profiles = {
        '2330': {'base_price': 600, 'volatility': 0.02, 'trend': 0.0002},  # 台積電
        '2317': {'base_price': 100, 'volatility': 0.025, 'trend': 0.0001}, # 鴻海
        '2454': {'base_price': 800, 'volatility': 0.03, 'trend': 0.0003},  # 聯發科
        '1301': {'base_price': 80, 'volatility': 0.02, 'trend': 0.0001},   # 台塑
        '2382': {'base_price': 150, 'volatility': 0.025, 'trend': 0.0002}, # 廣達
    }
    
    # 獲取股票特性，如果不在列表中則使用默認值
    profile = stock_profiles.get(stock_code, {'base_price': 50, 'volatility': 0.025, 'trend': 0.0001})
    
    # 生成價格數據
    np.random.seed(int(stock_code) if stock_code.isdigit() else 42)  # 使用股票代碼作為隨機種子
    
    prices = []
    current_price = profile['base_price']
    
    for i, date in enumerate(dates):
        # 添加趨勢和隨機波動
        daily_change = np.random.normal(profile['trend'], profile['volatility'])
        current_price = current_price * (1 + daily_change)
        
        # 確保價格不會變成負數
        current_price = max(current_price, profile['base_price'] * 0.3)
        
        # 生成 OHLC 數據
        high = current_price * (1 + abs(np.random.normal(0, 0.01)))
        low = current_price * (1 - abs(np.random.normal(0, 0.01)))
        open_price = current_price * (1 + np.random.normal(0, 0.005))
        close_price = current_price
        
        # 確保 OHLC 邏輯正確
        high = max(high, open_price, close_price)
        low = min(low, open_price, close_price)
        
        # 生成成交量（基於價格變化）
        volume_base = 10000000  # 1000萬股基礎量
        volume_multiplier = 1 + abs(daily_change) * 10  # 價格變化越大，成交量越大
        volume = int(volume_base * volume_multiplier * np.random.uniform(0.5, 2.0))
        
        prices.append({
            'Date': date,
            'Open': round(open_price, 2),
            'High': round(high, 2),
            'Low': round(low, 2),
            'Close': round(close_price, 2),
            'Volume': volume
        })
    
    df = pd.DataFrame(prices)
    df['Date'] = pd.to_datetime(df['Date'])
    
    st.success(f"✅ 生成股票 {stock_code} 的示例價格數據 ({len(df)} 筆記錄)")
    st.info(f"📅 數據期間: {df['Date'].min().strftime('%Y-%m-%d')} ~ {df['Date'].max().strftime('%Y-%m-%d')}")
    st.warning("⚠️ 這是模擬數據，僅供演示使用")
    
    return df

# 獲取股票歷史價格 - 使用本地TWSE數據庫
@st.cache_data
def get_stock_price_data(stock_code, period="1y"):
    """從本地TWSE數據庫獲取股票歷史價格數據"""
    
    # 清理股票代碼
    clean_code = stock_code.replace('.TW', '').strip()
    
    # 本地數據文件路徑
    data_file = f'data/stock_prices/{clean_code}_price_data.csv'
    
    try:
        if not os.path.exists(data_file):
            st.warning(f"⚠️ 找不到股票 {clean_code} 的本地數據文件，使用示例數據")
            return generate_demo_price_data(clean_code, period)
        
        # 讀取本地數據
        df = pd.read_csv(data_file)
        
        if df.empty:
            st.error(f"❌ 股票 {clean_code} 的數據文件為空")
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
        elif period == "5y":
            start_date = end_date - timedelta(days=1825)
        else:
            start_date = end_date - timedelta(days=365)
        
        # 篩選期間內的數據
        filtered_df = df[df['Date'] >= start_date].copy()
        filtered_df = filtered_df.sort_values('Date').reset_index(drop=True)
        
        if len(filtered_df) < 50:
            st.warning(f"⚠️ 股票 {clean_code} 在指定期間內的數據不足 (只有 {len(filtered_df)} 筆)")
            st.info("💡 建議選擇更長的時間期間或檢查數據完整性")
            return None
        
        st.success(f"✅ 成功從本地數據庫載入 {clean_code} 的數據 ({len(filtered_df)} 筆記錄)")
        st.info(f"📅 數據期間: {filtered_df['Date'].min().strftime('%Y-%m-%d')} ~ {filtered_df['Date'].max().strftime('%Y-%m-%d')}")
        
        return filtered_df
        
    except Exception as e:
        st.error(f"❌ 讀取股票 {clean_code} 數據失敗: {str(e)}")
        return None

# 獲取可用股票列表
@st.cache_data
def get_available_stocks():
    """獲取本地數據庫中可用的股票列表"""
    try:
        data_dir = 'data/stock_prices'
        if not os.path.exists(data_dir):
            # 如果沒有本地數據目錄，返回示例股票列表
            return get_demo_available_stocks()
        
        files = glob.glob(os.path.join(data_dir, '*_price_data.csv'))
        available_stocks = []
        
        for file in files:
            stock_code = os.path.basename(file).replace('_price_data.csv', '')
            try:
                df = pd.read_csv(file)
                if len(df) > 50:  # 至少要有50筆數據
                    df['Date'] = pd.to_datetime(df['Date'])
                    available_stocks.append({
                        'code': stock_code,
                        'records': len(df),
                        'start_date': df['Date'].min(),
                        'end_date': df['Date'].max(),
                        'latest_price': df['Close'].iloc[-1] if len(df) > 0 else 0
                    })
            except:
                continue
        
        # 如果找到的股票太少，使用示例數據
        if len(available_stocks) < 10:
            return get_demo_available_stocks()
        
        # 按股票代碼排序
        available_stocks.sort(key=lambda x: x['code'])
        return available_stocks
        
    except Exception as e:
        st.error(f"❌ 獲取可用股票列表失敗: {str(e)}")
        return get_demo_available_stocks()

# 獲取示例可用股票列表
@st.cache_data
def get_demo_available_stocks():
    """為雲端版本提供示例可用股票列表"""
    demo_stocks = [
        {'code': '2330', 'records': 260, 'start_date': datetime.now() - timedelta(days=365), 
         'end_date': datetime.now(), 'latest_price': 600.0},
        {'code': '2317', 'records': 260, 'start_date': datetime.now() - timedelta(days=365), 
         'end_date': datetime.now(), 'latest_price': 100.0},
        {'code': '2454', 'records': 260, 'start_date': datetime.now() - timedelta(days=365), 
         'end_date': datetime.now(), 'latest_price': 800.0},
        {'code': '1301', 'records': 260, 'start_date': datetime.now() - timedelta(days=365), 
         'end_date': datetime.now(), 'latest_price': 80.0},
        {'code': '2382', 'records': 260, 'start_date': datetime.now() - timedelta(days=365), 
         'end_date': datetime.now(), 'latest_price': 150.0},
    ]
    return demo_stocks

# 計算布林通道策略
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

# 布林通道策略回測
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
    
    # 記錄每日資產價值
    portfolio_values = []
    
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
        
        # 計算當前投資組合價值
        if position == 1:
            portfolio_value = capital + shares * current_price
        else:
            portfolio_value = capital
        
        portfolio_values.append({
            'Date': df.iloc[i]['Date'],
            'Portfolio_Value': portfolio_value,
            'Stock_Price': current_price
        })
    
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
        'portfolio_values': pd.DataFrame(portfolio_values),
        'df_with_indicators': df
    }

# 突破策略相關函數
def calculate_breakout_indicators(df):
    """計算突破策略需要的技術指標"""
    if df is None or len(df) < 60:
        return df
    
    df = df.copy()
    
    # 計算移動平均線
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['MA60'] = df['Close'].rolling(window=60).mean()
    df['MA10'] = df['Close'].rolling(window=10).mean()
    
    # 計算20日最高價
    df['High20'] = df['High'].rolling(window=20).max()
    
    # 計算5日平均成交量
    df['Volume_MA5'] = df['Volume'].rolling(window=5).mean()
    
    return df

def breakout_strategy_backtest(df, initial_capital=100000, stop_loss_pct=6, take_profit_pct=15):
    """突破策略回測"""
    if df is None or len(df) < 60:
        return None
    
    # 添加技術指標
    df = calculate_breakout_indicators(df)
    
    # 去除NaN值
    df = df.dropna().copy()
    
    if len(df) < 10:
        return None
    
    # 初始化變量
    position = 0  # 0: 無持股, 1: 持股
    capital = initial_capital
    shares = 0
    trades = []
    entry_price = 0
    
    # 記錄每日資產價值
    portfolio_values = []
    
    for i in range(1, len(df)):
        current_row = df.iloc[i]
        prev_row = df.iloc[i-1]
        
        current_price = current_row['Close']
        current_high = current_row['High']
        current_volume = current_row['Volume']
        
        # 進場條件檢查
        if position == 0:
            # 1. 趨勢判斷：股價站上20日與60日均線
            trend_condition = (current_price > current_row['MA20'] and 
                             current_price > current_row['MA60'])
            
            # 2. 突破進場：當天收盤價 > 最近20日高點
            breakout_condition = current_price > prev_row['High20']
            
            # 3. 成交量過濾：進場日成交量 > 前5日平均量
            volume_condition = current_volume > current_row['Volume_MA5']
            
            # 所有條件滿足才進場
            if trend_condition and breakout_condition and volume_condition:
                # 買入
                shares = capital // current_price
                if shares > 0:
                    entry_price = current_price
                    capital -= shares * current_price
                    position = 1
                    trades.append({
                        'Date': current_row['Date'],
                        'Action': 'BUY',
                        'Price': current_price,
                        'Shares': shares,
                        'Capital': capital,
                        'Signal': 'Breakout + Volume + Trend'
                    })
        
        # 出場條件檢查
        elif position == 1:
            exit_signal = ""
            should_exit = False
            
            # 1. 停損：收盤價跌破進場價 - 6%
            stop_loss_price = entry_price * (1 - stop_loss_pct / 100)
            if current_price <= stop_loss_price:
                should_exit = True
                exit_signal = f"Stop Loss (-{stop_loss_pct:.1f}%)"
            
            # 2. 停利：達到 +15% 報酬
            elif current_price >= entry_price * (1 + take_profit_pct / 100):
                should_exit = True
                exit_signal = f"Take Profit (+{take_profit_pct:.1f}%)"
            
            # 3. 追蹤出場：跌破10日均線
            elif current_price < current_row['MA10']:
                should_exit = True
                exit_signal = "Below MA10"
            
            if should_exit:
                # 賣出
                capital += shares * current_price
                return_pct = (current_price - entry_price) / entry_price * 100
                trades.append({
                    'Date': current_row['Date'],
                    'Action': 'SELL',
                    'Price': current_price,
                    'Shares': shares,
                    'Capital': capital,
                    'Signal': exit_signal,
                    'Return': return_pct
                })
                shares = 0
                position = 0
                entry_price = 0
        
        # 計算當前投資組合價值
        if position == 1:
            portfolio_value = capital + shares * current_price
        else:
            portfolio_value = capital
        
        portfolio_values.append({
            'Date': current_row['Date'],
            'Portfolio_Value': portfolio_value,
            'Stock_Price': current_price
        })
    
    # 如果最後還持有股票，以最後價格賣出
    if position == 1:
        final_price = df.iloc[-1]['Close']
        return_pct = (final_price - entry_price) / entry_price * 100
        capital += shares * final_price
        trades.append({
            'Date': df.iloc[-1]['Date'],
            'Action': 'SELL (Final)',
            'Price': final_price,
            'Shares': shares,
            'Capital': capital,
            'Signal': 'Final Exit',
            'Return': return_pct
        })
    
    return {
        'final_capital': capital,
        'total_return': (capital - initial_capital) / initial_capital * 100,
        'trades': trades,
        'portfolio_values': pd.DataFrame(portfolio_values),
        'df_with_indicators': df
    }

# 顯示回測結果的統一UI函數
def show_backtest_results_ui(backtest_result, stock_code, stock_name, strategy_name, initial_capital, stop_loss_pct=None, take_profit_pct=None):
    """統一顯示回測結果的UI"""
    # 顯示回測結果
    st.subheader("📊 回測結果")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "初始資金",
            f"${initial_capital:,.0f}",
        )
    
    with col2:
        st.metric(
            "最終資金",
            f"${backtest_result['final_capital']:,.0f}",
        )
    
    with col3:
        total_return = backtest_result['total_return']
        st.metric(
            "總報酬率",
            f"{total_return:.2f}%",
            delta=f"{total_return:.2f}%"
        )
    
    with col4:
        num_trades = len(backtest_result['trades'])
        st.metric(
            "交易次數",
            f"{num_trades} 次"
        )
    
    # 策略表現圖表
    st.subheader(f"📈 {strategy_name}表現圖")
    
    df_with_indicators = backtest_result['df_with_indicators']
    
    fig = go.Figure()
    
    # 股價線
    fig.add_trace(go.Scatter(
        x=df_with_indicators['Date'],
        y=df_with_indicators['Close'],
        mode='lines',
        name='收盤價',
        line=dict(color='black', width=2)
    ))
    
    # 根據策略類型添加不同的指標線
    if strategy_name == "布林通道策略":
        # 布林通道
        fig.add_trace(go.Scatter(
            x=df_with_indicators['Date'],
            y=df_with_indicators['Upper_Band'],
            mode='lines',
            name='上軌',
            line=dict(color='red', width=1, dash='dash')
        ))
        
        fig.add_trace(go.Scatter(
            x=df_with_indicators['Date'],
            y=df_with_indicators['MA'],
            mode='lines',
            name='中軌(MA)',
            line=dict(color='blue', width=1)
        ))
        
        fig.add_trace(go.Scatter(
            x=df_with_indicators['Date'],
            y=df_with_indicators['Lower_Band'],
            mode='lines',
            name='下軌',
            line=dict(color='green', width=1, dash='dash')
        ))
    
    elif strategy_name == "突破策略":
        # 移動平均線
        fig.add_trace(go.Scatter(
            x=df_with_indicators['Date'],
            y=df_with_indicators['MA20'],
            mode='lines',
            name='MA20',
            line=dict(color='blue', width=1)
        ))
        
        fig.add_trace(go.Scatter(
            x=df_with_indicators['Date'],
            y=df_with_indicators['MA60'],
            mode='lines',
            name='MA60',
            line=dict(color='orange', width=1)
        ))
        
        fig.add_trace(go.Scatter(
            x=df_with_indicators['Date'],
            y=df_with_indicators['MA10'],
            mode='lines',
            name='MA10',
            line=dict(color='purple', width=1, dash='dot')
        ))
        
        # 20日最高點線
        fig.add_trace(go.Scatter(
            x=df_with_indicators['Date'],
            y=df_with_indicators['High20'],
            mode='lines',
            name='20日最高',
            line=dict(color='red', width=1, dash='dash')
        ))
    
    # 標記買賣點
    trades_df = pd.DataFrame(backtest_result['trades'])
    if not trades_df.empty:
        buy_trades = trades_df[trades_df['Action'] == 'BUY']
        sell_trades = trades_df[trades_df['Action'].str.contains('SELL')]
        
        if not buy_trades.empty:
            fig.add_trace(go.Scatter(
                x=buy_trades['Date'],
                y=buy_trades['Price'],
                mode='markers',
                name='買入',
                marker=dict(color='green', size=10, symbol='triangle-up'),
                text=buy_trades.get('Signal', ['買入'] * len(buy_trades)),
                hovertemplate='<b>買入</b><br>日期: %{x}<br>價格: %{y:.2f}<br>信號: %{text}'
            ))
        
        if not sell_trades.empty:
            sell_signals = sell_trades.get('Signal', ['賣出'] * len(sell_trades))
            returns = sell_trades.get('Return', [0] * len(sell_trades))
            hover_text = [f"{signal}<br>報酬: {ret:.2f}%" for signal, ret in zip(sell_signals, returns)]
            
            fig.add_trace(go.Scatter(
                x=sell_trades['Date'],
                y=sell_trades['Price'],
                mode='markers',
                name='賣出',
                marker=dict(color='red', size=10, symbol='triangle-down'),
                text=hover_text,
                hovertemplate='<b>賣出</b><br>日期: %{x}<br>價格: %{y:.2f}<br>%{text}'
            ))
    
    fig.update_layout(
        title=f"{stock_code} - {stock_name} {strategy_name}回測",
        xaxis_title="日期",
        yaxis_title="股價 (TWD)",
        hovermode='x unified',
        height=600,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # 投資組合價值曲線
    if not backtest_result['portfolio_values'].empty:
        st.subheader("💰 投資組合價值變化")
        
        try:
            portfolio_df = backtest_result['portfolio_values']
            
            # 检查必要的列是否存在
            required_columns = ['Date', 'Portfolio_Value', 'Stock_Price']
            missing_columns = [col for col in required_columns if col not in portfolio_df.columns]
            
            if missing_columns:
                st.error(f"❌ 投資組合數據缺少必要欄位: {missing_columns}")
                st.info("💡 請重新執行回測以獲得完整數據")
                return
            
            # 確保Date欄位是datetime格式
            if not pd.api.types.is_datetime64_any_dtype(portfolio_df['Date']):
                portfolio_df['Date'] = pd.to_datetime(portfolio_df['Date'])
            
            # 計算買入持有策略比較
            first_price = portfolio_df.iloc[0]['Stock_Price']
            last_price = portfolio_df.iloc[-1]['Stock_Price']
            
            if first_price <= 0:
                st.error("❌ 股價數據異常，無法計算買入持有策略")
                return
                
            buy_hold_return = (last_price - first_price) / first_price * 100
            buy_hold_final = initial_capital * (1 + buy_hold_return / 100)
            
            portfolio_df['Buy_Hold_Value'] = initial_capital * (portfolio_df['Stock_Price'] / first_price)
            
            # 創建雙軸圖表 - 修復顏色和主題
            fig2 = go.Figure()
            
            # 添加投資組合價值線 (主軸)
            fig2.add_trace(go.Scatter(
                x=portfolio_df['Date'],
                y=portfolio_df['Portfolio_Value'],
                mode='lines',
                name=f'{strategy_name}表現',
                line=dict(color='#1f77b4', width=3),  # 藍色
                yaxis='y'
            ))
            
            # 添加買入持有策略線 (主軸)
            fig2.add_trace(go.Scatter(
                x=portfolio_df['Date'],
                y=portfolio_df['Buy_Hold_Value'],
                mode='lines',
                name='買入持有策略',
                line=dict(color='#ff7f0e', width=2, dash='dash'),  # 橙色虛線
                yaxis='y'
            ))
            
            # 添加股價走勢線 (次軸)
            fig2.add_trace(go.Scatter(
                x=portfolio_df['Date'],
                y=portfolio_df['Stock_Price'],
                mode='lines',
                name='股價走勢',
                line=dict(color='#2ca02c', width=1, dash='dot'),  # 綠色點線
                yaxis='y2',
                opacity=0.7
            ))
            
            # 設置雙軸布局
            fig2.update_layout(
                title={
                    'text': f"📈 投資組合價值變化 vs 股價走勢",
                    'x': 0.5,
                    'font': {'size': 18, 'color': '#2c3e50'}
                },
                xaxis_title="日期",
                yaxis=dict(
                    title="投資組合價值 (TWD)",
                    side="left",
                    showgrid=True,
                    gridcolor='lightgray',
                    tickformat=',.0f'
                ),
                yaxis2=dict(
                    title="股價 (TWD)",
                    side="right",
                    overlaying="y",
                    showgrid=False,
                    tickformat='.2f'
                ),
                hovermode='x unified',
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1,
                    bgcolor="rgba(255,255,255,0.8)"
                ),
                plot_bgcolor='white',
                paper_bgcolor='white',
                font=dict(family="Arial, sans-serif"),
                height=500
            )
            
            st.plotly_chart(fig2, use_container_width=True)
            
            # 策略比較表 - 增強視覺效果
            st.subheader("📋 策略比較")
            
            strategy_performance = total_return
            buy_hold_performance = buy_hold_return
            outperformance = strategy_performance - buy_hold_performance
            
            comparison_data = {
                "策略": [strategy_name, "買入持有策略", "超額表現"],
                "總報酬率 (%)": [
                    f"{strategy_performance:.2f}%", 
                    f"{buy_hold_performance:.2f}%",
                    f"{outperformance:.2f}%"
                ],
                "最終資金": [
                    f"${backtest_result['final_capital']:,.0f}", 
                    f"${buy_hold_final:,.0f}",
                    f"${backtest_result['final_capital'] - buy_hold_final:,.0f}"
                ],
                "年化報酬": [
                    f"{(strategy_performance / (len(portfolio_df) / 252)):.2f}%" if len(portfolio_df) > 252 else f"{strategy_performance:.2f}%",
                    f"{(buy_hold_performance / (len(portfolio_df) / 252)):.2f}%" if len(portfolio_df) > 252 else f"{buy_hold_performance:.2f}%",
                    f"{(outperformance / (len(portfolio_df) / 252)):.2f}%" if len(portfolio_df) > 252 else f"{outperformance:.2f}%"
                ]
            }
            
            comparison_df = pd.DataFrame(comparison_data)
            
            # 使用彩色展示
            def highlight_performance(val):
                if '超額表現' in str(val):
                    return 'background-color: #e8f5e8' if '超額表現' in str(val) else ''
                return ''
            
            styled_df = comparison_df.style.applymap(highlight_performance)
            st.dataframe(styled_df, use_container_width=True)
            
            # 如果是突破策略，添加風險參數資訊
            if strategy_name == "突破策略" and stop_loss_pct and take_profit_pct:
                st.info(f"🎯 策略參數: 停損 -{stop_loss_pct}% | 停利 +{take_profit_pct}%")
            
        except Exception as e:
            st.error(f"❌ 顯示投資組合價值變化失敗: {str(e)}")
            st.info("💡 這可能是數據格式問題，請嘗試重新執行回測")
            
    else:
        st.warning("⚠️ 沒有投資組合價值數據可顯示")
        st.info("💡 請確保回測已成功執行並生成了投資組合數據")
    
    # 交易記錄
    if backtest_result['trades']:
        st.subheader("📝 交易記錄")
        trades_df = pd.DataFrame(backtest_result['trades'])
        
        # 格式化交易記錄表格
        if 'Return' in trades_df.columns:
            trades_df['Return'] = trades_df['Return'].apply(lambda x: f"{x:.2f}%" if pd.notna(x) else "-")
        if 'Price' in trades_df.columns:
            trades_df['Price'] = trades_df['Price'].apply(lambda x: f"{x:.2f}")
        if 'Capital' in trades_df.columns:
            trades_df['Capital'] = trades_df['Capital'].apply(lambda x: f"{x:,.0f}")
        
        st.dataframe(trades_df, use_container_width=True)
        
        # 交易統計
        if len(trades_df) > 1:
            st.subheader("📊 交易統計")
            
            # 計算勝率
            if 'Return' in backtest_result['trades'][0]:
                returns = [trade.get('Return', 0) for trade in backtest_result['trades'] if trade.get('Return') is not None]
                if returns:
                    win_trades = len([r for r in returns if r > 0])
                    total_trades = len(returns)
                    win_rate = (win_trades / total_trades * 100) if total_trades > 0 else 0
                    
                    avg_return = sum(returns) / len(returns) if returns else 0
                    max_return = max(returns) if returns else 0
                    min_return = min(returns) if returns else 0
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("勝率", f"{win_rate:.1f}%")
                    with col2:
                        st.metric("平均報酬", f"{avg_return:.2f}%")
                    with col3:
                        st.metric("最大獲利", f"{max_return:.2f}%")
                    with col4:
                        st.metric("最大虧損", f"{min_return:.2f}%")

def show_single_stock_backtest_page(stock_data):
    """個股策略回測頁面"""
    st.markdown('<div class="page-header">📊 個股策略回測</div>', unsafe_allow_html=True)
    
    # 載入本地數據庫
    available_stocks = get_available_stocks()
    
    if not available_stocks:
        st.warning("⚠️ 本地TWSE數據庫為空！")
        st.info("請先下載股票數據：")
        with st.expander("📥 如何下載數據", expanded=True):
            st.markdown("""
            **步驟 1: 運行數據下載器**
            ```bash
            python twse_data_downloader.py
            ```
            
            **步驟 2: 選擇下載選項**
            - 選項 1: 下載所有股票數據 (推薦)
            - 選項 2: 查看可用股票
            - 選項 3: 下載單一股票
            
            **注意事項:**
            - 首次下載可能需要較長時間
            - 數據會保存在 `data/stock_prices/` 目錄
            - 支援增量更新，避免重複下載
            """)
        
        return
    
    # 顯示數據庫狀態
    total_stocks_in_db = len(stock_data) if stock_data is not None else 765
    st.success(f"✅ 本地數據庫已載入 {len(available_stocks)} 支股票的價格數據")
    st.info(f"📊 完整股票資料庫：{total_stocks_in_db} 支股票 | 可回測股票：{len(available_stocks)} 支")
    
    # 直接顯示單股回測功能
    show_single_stock_backtest(stock_data, available_stocks)

def show_batch_backtest_page(stock_data):
    """批量回測頁面"""
    st.markdown('<div class="page-header">🎯 批量回測</div>', unsafe_allow_html=True)
    
    # 載入本地數據庫
    available_stocks = get_available_stocks()
    
    if not available_stocks:
        st.warning("⚠️ 本地TWSE數據庫為空！")
        st.info("請先下載股票數據：")
        with st.expander("📥 如何下載數據", expanded=True):
            st.markdown("""
            **步驟 1: 運行數據下載器**
            ```bash
            python twse_data_downloader.py
            ```
            
            **步驟 2: 選擇下載選項**
            - 選項 1: 下載所有股票數據 (推薦)
            - 選項 2: 查看可用股票
            - 選項 3: 下載單一股票
            
            **注意事項:**
            - 首次下載可能需要較長時間
            - 數據會保存在 `data/stock_prices/` 目錄
            - 支援增量更新，避免重複下載
            """)
        
        return
    
    # 顯示數據庫狀態
    total_stocks_in_db = len(stock_data) if stock_data is not None else 765
    st.success(f"✅ 本地數據庫已載入 {len(available_stocks)} 支股票的價格數據")
    st.info(f"📊 完整股票資料庫：{total_stocks_in_db} 支股票 | 可回測股票：{len(available_stocks)} 支")
    
    # 直接顯示批量回測功能
    show_batch_backtest_execution(stock_data, available_stocks)

def show_single_stock_backtest(stock_data, available_stocks):
    """單股回測功能"""
    # 股票選擇區域
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.subheader("🎯 選擇股票")
        
        # 股票代碼輸入方式選擇
        input_method = st.radio(
            "選擇輸入方式:",
            ["📝 手動輸入股票代碼", "📋 從可用列表選擇"],
            horizontal=True
        )
        
        if input_method == "📝 手動輸入股票代碼":
            stock_input = st.text_input(
                "請輸入股票代碼 (例如: 2330, 2454, 0050)",
                value="2330",
                help="輸入台灣股票代碼，不需要.TW後綴"
            )
        else:
            # 創建選擇選項
            stock_options = []
            for stock in available_stocks:
                latest_date = stock['end_date'].strftime('%Y-%m-%d')
                option_text = f"{stock['code']} (最新: {stock['latest_price']:.2f}, 更新至: {latest_date})"
                stock_options.append(option_text)
            
            selected_option = st.selectbox(
                "選擇股票:",
                stock_options,
                help="從本地數據庫中選擇可用的股票"
            )
            
            # 提取股票代碼
            stock_input = selected_option.split(' ')[0] if selected_option else "2330"
    
    with col2:
        st.subheader("⏰ 回測期間")
        period = st.selectbox(
            "選擇期間",
            ["1y", "2y", "3y", "5y"],
            index=0,
            help="選擇回測的時間範圍"
        )
        
        # 顯示可用股票統計
        with st.expander("📊 數據庫統計", expanded=False):
            total_records = sum(stock['records'] for stock in available_stocks)
            avg_records = total_records // len(available_stocks) if available_stocks else 0
            
            st.metric("總股票數", len(available_stocks))
            st.metric("總交易記錄", f"{total_records:,}")
            st.metric("平均記錄數", f"{avg_records:,}")
            
            # 最新更新時間
            if available_stocks:
                latest_update = max(stock['end_date'] for stock in available_stocks)
                st.metric("最新數據", latest_update.strftime('%Y-%m-%d'))
    
    if stock_input:
        # 獲取股票資訊
        stock_code = stock_input.strip()
        
        # 從本地數據庫查找股票資訊
        local_stock_info = None
        for stock in available_stocks:
            if stock['code'] == stock_code:
                local_stock_info = stock
                break
        
        # 從股票篩選數據查找名稱
        stock_name = "未知"
        if stock_data is not None:
            stock_info = stock_data[stock_data['stock_code'].str.contains(stock_code, na=False)]
            if not stock_info.empty:
                stock_name = stock_info.iloc[0]['name']
        
        # 顯示股票資訊
        if local_stock_info:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("股票代碼", stock_code)
            with col2:
                st.metric("股票名稱", stock_name)
            with col3:
                st.metric("數據筆數", f"{local_stock_info['records']:,}")
            with col4:
                st.metric("最新價格", f"{local_stock_info['latest_price']:.2f}")
            
            st.info(f"📅 數據期間: {local_stock_info['start_date'].strftime('%Y-%m-%d')} ~ {local_stock_info['end_date'].strftime('%Y-%m-%d')}")
        else:
            st.warning(f"⚠️ 本地數據庫中找不到股票 {stock_code}")
            st.info("💡 請檢查股票代碼是否正確，或使用數據下載器下載該股票數據")
            return
        
        # 獲取股價數據
        with st.spinner(f"正在從本地數據庫載入 {stock_code} 的數據..."):
            price_data = get_stock_price_data(stock_code, period)
        
        if price_data is not None:
            # 顯示股價曲線圖
            st.subheader("📈 股價走勢圖")
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=price_data['Date'],
                y=price_data['Close'],
                mode='lines',
                name='收盤價',
                line=dict(color='blue', width=2)
            ))
            
            fig.update_layout(
                title=f"{stock_code} - {stock_name} 股價走勢 ({period})",
                xaxis_title="日期",
                yaxis_title="股價 (TWD)",
                hovermode='x unified',
                height=500
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # 策略設定
            st.subheader("🎯 交易策略選擇")
            
            # 策略選擇
            st.subheader("📊 策略選擇")
            strategy = st.selectbox(
                "選擇回測策略：",
                ["布林通道策略", "突破策略", "日內交易策略 (CPR + Camarilla)"],
                key="single_strategy_select"
            )
            
            if strategy == "布林通道策略":
                # 布林通道策略設定
                st.markdown("### 📊 布林通道策略參數")
                col1, col2, col3 = st.columns(3)
                with col1:
                    bb_window = st.number_input(
                        "移動平均週期", 
                        min_value=5, 
                        max_value=50, 
                        value=20,
                        help="計算移動平均線的天數"
                    )
                with col2:
                    bb_std = st.number_input(
                        "標準差倍數", 
                        min_value=1.0, 
                        max_value=3.0, 
                        value=2.0, 
                        step=0.1,
                        help="布林通道寬度的標準差倍數"
                    )
                with col3:
                    initial_capital = st.number_input(
                        "初始資金", 
                        min_value=10000, 
                        max_value=10000000, 
                        value=100000, 
                        step=10000,
                        help="回測的初始投資金額"
                    )
                
                # 策略說明
                with st.expander("📖 布林通道策略說明", expanded=False):
                    st.markdown(f"""
                    **布林通道策略原理:**
                    
                    1. **指標計算:**
                       - 中軌: {bb_window}日移動平均線
                       - 上軌: 中軌 + {bb_std}倍標準差
                       - 下軌: 中軌 - {bb_std}倍標準差
                    
                    2. **交易信號:**
                       - **買入信號**: 股價觸及下軌後反彈
                       - **賣出信號**: 股價觸及上軌
                    
                    3. **策略邏輯:**
                       - 當股價跌至下軌時，認為超賣，等待反彈買入
                       - 當股價漲至上軌時，認為超買，賣出獲利
                       - 利用股價在通道內震盪的特性進行交易
                    """)
                
                # 執行回測
                if st.button("🚀 執行布林通道策略回測", type="primary"):
                    with st.spinner("正在執行策略回測..."):
                        backtest_result = bollinger_strategy_backtest(
                            price_data.copy(), 
                            initial_capital=initial_capital
                        )
                    
                    if backtest_result:
                        # 顯示回測結果的代碼保持不變
                        show_backtest_results_ui(backtest_result, stock_code, stock_name, "布林通道策略", initial_capital)
                    else:
                        st.error("❌ 策略回測失敗，數據可能不足或存在問題")
            
            elif strategy == "突破策略":
                # 突破策略設定
                st.markdown("### 🚀 突破策略參數")
                col1, col2, col3 = st.columns(3)
                with col1:
                    stop_loss_pct = st.number_input(
                        "停損百分比 (%)", 
                        min_value=1.0, 
                        max_value=20.0, 
                        value=6.0,
                        step=0.5,
                        help="跌破進場價多少%時停損"
                    )
                with col2:
                    take_profit_pct = st.number_input(
                        "停利百分比 (%)", 
                        min_value=5.0, 
                        max_value=50.0, 
                        value=15.0, 
                        step=1.0,
                        help="達到多少%獲利時停利"
                    )
                with col3:
                    initial_capital = st.number_input(
                        "初始資金", 
                        min_value=10000, 
                        max_value=10000000, 
                        value=100000, 
                        step=10000,
                        help="回測的初始投資金額",
                        key="breakout_capital"
                    )
                
                # 策略說明
                with st.expander("📖 突破策略說明", expanded=False):
                    st.markdown(f"""
                    **突破策略原理 (順勢+突破型):**
                    
                    **1️⃣ 進場條件 (三個條件須同時滿足):**
                    - 🔸 **趨勢判斷**: 股價站上 20日與60日均線
                    - 🔸 **突破進場**: 當天收盤價 > 最近 20日高點
                    - 🔸 **成交量過濾**: 進場日成交量 > 前 5 日平均量 (代表主力參與)
                    
                    **2️⃣ 出場條件 (滿足任一條件即出場):**
                    - 🔴 **停損**: 收盤價跌破進場價 -{stop_loss_pct:.1f}% 即隔天出場
                    - 🟢 **停利**: 達到 +{take_profit_pct:.1f}% 報酬即獲利了結
                    - 🟡 **追蹤出場**: 跌破 10 日均線可分批減碼或出清
                    
                    **3️⃣ 策略特色:**
                    - 🎯 順勢操作，跟隨趨勢方向
                    - 📈 突破創新高時進場，捕捉強勢股
                    - 💪 量價配合，確保主力參與
                    - 🛡️ 明確的風險控制機制
                    """)
                
                # 執行回測
                if st.button("🚀 執行突破策略回測", type="primary"):
                    with st.spinner("正在執行策略回測..."):
                        backtest_result = breakout_strategy_backtest(
                            price_data.copy(), 
                            initial_capital=initial_capital,
                            stop_loss_pct=stop_loss_pct,
                            take_profit_pct=take_profit_pct
                        )
                    
                    if backtest_result:
                        # 顯示回測結果
                        show_backtest_results_ui(backtest_result, stock_code, stock_name, "突破策略", initial_capital, stop_loss_pct, take_profit_pct)
                    else:
                        st.error("❌ 策略回測失敗，數據可能不足或存在問題")

            elif strategy == "日內交易策略 (CPR + Camarilla)":
                # 日內交易策略設定
                st.markdown("### ⚡ 日內交易策略參數")
                
                col1, col2 = st.columns(2)
                with col1:
                    initial_capital = st.number_input(
                        "初始資本 💰",
                        min_value=10000,
                        max_value=10000000,
                        value=100000,
                        step=10000,
                        key="intraday_capital"
                    )
                
                with col2:
                    volume_threshold = st.slider(
                        "量能突破倍數 📊",
                        min_value=1.0,
                        max_value=3.0,
                        value=1.2,
                        step=0.1,
                        key="intraday_volume_threshold",
                        help="突破時需要的成交量倍數（相對於10日平均量）"
                    )
                
                # 策略說明
                with st.expander("📋 策略說明", expanded=False):
                    st.markdown("""
                    **日內交易策略 (CPR + Camarilla Pivot Points)**
                    
                    **指標計算：**
                    - **CPR指標：**
                      - 中樞 (PP) = (H + L + C) / 3
                      - 上軌 (BC) = (H + L) / 2  
                      - 下軌 (TC) = PP × 2 - BC
                    
                    - **Camarilla樞軸點：**
                      - 阻力位 H1-H4：C + (H-L) × 1.1 × [1/12, 1/6, 1/4, 1/2]
                      - 支撐位 L1-L4：C - (H-L) × 1.1 × [1/12, 1/6, 1/4, 1/2]
                    
                    **進場條件：**
                    - **做多：** 突破CPR上軌(BC) + 放量 + 站上H1
                    - **做空：** 跌破CPR下軌(TC) + 放量 + 失守L1
                    
                    **出場條件：**
                    - **停利：** 多倉觸及H3，空倉觸及L3
                    - **停損：** 多倉跌破L1或PP，空倉突破H1或PP
                    """)
                
                if st.button("🚀 執行日內交易策略回測", key="intraday_backtest_btn"):
                    with st.spinner("⚡ 執行日內交易策略回測中..."):
                        result = intraday_strategy_backtest(
                            price_data.copy(), 
                            initial_capital=initial_capital,
                            volume_threshold=volume_threshold
                        )
                        
                        if result:
                            display_intraday_strategy_results(result, "日內交易策略")
                        else:
                            st.error("❌ 策略回測失敗，數據可能不足或存在問題")

def show_batch_backtest_execution(stock_data, available_stocks):
    """批量回測執行功能"""
    st.subheader("🎯 批量回測設定")
    
    # 回測範圍選擇
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📊 選擇回測範圍")
        
        backtest_scope = st.radio(
            "選擇要回測的股票範圍:",
            ["🎯 全部股票", "📝 指定股票列表", "🔍 篩選股票"],
            help="選擇批量回測的範圍"
        )
        
        if backtest_scope == "📝 指定股票列表":
            stock_codes_input = st.text_area(
                "輸入股票代碼 (每行一個):",
                value="2330\n2317\n2454\n0050\n0056",
                help="每行輸入一個股票代碼，不需要.TW後綴"
            )
            
            selected_stocks = [code.strip() for code in stock_codes_input.split('\n') if code.strip()]
            available_for_backtest = [stock['code'] for stock in available_stocks if stock['code'] in selected_stocks]
            
            st.info(f"📊 指定 {len(selected_stocks)} 支股票，其中 {len(available_for_backtest)} 支有完整數據可回測")
            
        elif backtest_scope == "🔍 篩選股票":
            if stock_data is not None:
                # 快速篩選選項
                filter_option = st.selectbox(
                    "選擇篩選條件:",
                    ["高ROE股票 (ROE>15%)", "高EPS股票 (EPS>2)", "大型股 (市值前100)", "自定義篩選"],
                    help="選擇預設篩選條件或自定義"
                )
                
                if filter_option == "高ROE股票 (ROE>15%)":
                    if 'ROE' in stock_data.columns or 'ROE(%)' in stock_data.columns:
                        roe_col = 'ROE' if 'ROE' in stock_data.columns else 'ROE(%)'
                        filtered_stocks = stock_data[stock_data[roe_col] > 15]['stock_code'].tolist()
                    else:
                        filtered_stocks = [stock['code'] for stock in available_stocks[:50]]  # 前50支作為示範
                        
                elif filter_option == "高EPS股票 (EPS>2)":
                    if 'EPS' in stock_data.columns:
                        filtered_stocks = stock_data[stock_data['EPS'] > 2]['stock_code'].tolist()
                    else:
                        filtered_stocks = [stock['code'] for stock in available_stocks[:50]]
                        
                elif filter_option == "大型股 (市值前100)":
                    filtered_stocks = [stock['code'] for stock in available_stocks[:100]]
                    
                else:  # 自定義篩選
                    max_stocks = st.slider("選擇股票數量上限:", 10, len(available_stocks), 50)
                    filtered_stocks = [stock['code'] for stock in available_stocks[:max_stocks]]
                
                available_for_backtest = [code for code in filtered_stocks if any(stock['code'] == code for stock in available_stocks)]
                st.info(f"📊 篩選出 {len(available_for_backtest)} 支股票可回測")
            else:
                st.warning("⚠️ 無法載入篩選數據，將使用前50支股票")
                available_for_backtest = [stock['code'] for stock in available_stocks[:50]]
        
        else:  # 全部股票
            available_for_backtest = [stock['code'] for stock in available_stocks]
            st.info(f"📊 將回測全部 {len(available_for_backtest)} 支股票")
    
    with col2:
        st.markdown("### ⚙️ 回測參數設定")
        
        # 策略選擇
        strategy_choice = st.selectbox(
            "選擇回測策略:",
            ["📊 布林通道策略", "🚀 突破策略", "⚡ 日內交易策略 (CPR + Camarilla)", "🎯 多策略比較"],
            help="選擇要使用的交易策略"
        )
        
        # 回測期間
        period = st.selectbox(
            "回測期間:",
            ["1y", "2y", "3y"],
            index=0,
            help="選擇回測的時間範圍"
        )
        
        # 初始資金
        initial_capital = st.number_input(
            "初始資金:",
            min_value=10000,
            max_value=1000000,
            value=100000,
            step=10000,
            help="每支股票的初始投資金額"
        )
        
        # 篩選條件
        min_return = st.number_input(
            "最低報酬率篩選 (%):",
            min_value=0.0,
            max_value=50.0,
            value=10.0,
            step=1.0,
            help="只顯示報酬率大於此值的股票"
        )
    
    # 策略參數設定
    if strategy_choice == "📊 布林通道策略":
        st.markdown("### 📊 布林通道策略參數")
        col1, col2 = st.columns(2)
        with col1:
            bb_window = st.number_input("移動平均週期", min_value=5, max_value=50, value=20, key="batch_bb_window")
        with col2:
            bb_std = st.number_input("標準差倍數", min_value=1.0, max_value=3.0, value=2.0, step=0.1, key="batch_bb_std")
    
    elif strategy_choice == "🚀 突破策略":
        st.markdown("### 🚀 突破策略參數")
        col1, col2 = st.columns(2)
        with col1:
            stop_loss_pct = st.number_input("停損百分比 (%)", min_value=1.0, max_value=20.0, value=6.0, step=0.5, key="batch_stop_loss")
        with col2:
            take_profit_pct = st.number_input("停利百分比 (%)", min_value=5.0, max_value=50.0, value=15.0, step=1.0, key="batch_take_profit")
    
    elif strategy_choice == "⚡ 日內交易策略 (CPR + Camarilla)":
        st.markdown("### ⚡ 日內交易策略參數")
        col1, col2 = st.columns(2)
        with col1:
            volume_threshold = st.slider("量能突破倍數", min_value=1.0, max_value=3.0, value=1.2, step=0.1, key="batch_volume_threshold")
        with col2:
            st.markdown("**策略說明:**")
            st.caption("結合CPR和Camarilla樞軸點的日內交易策略")
    
    # 執行批量回測
    if st.button("🚀 開始批量回測", type="primary", key="start_batch_backtest"):
        if len(available_for_backtest) == 0:
            st.error("❌ 沒有可回測的股票")
            return
        
        # 執行批量回測
        execute_batch_backtest(
            available_for_backtest=available_for_backtest,
            strategy_choice=strategy_choice,
            period=period,
            initial_capital=initial_capital,
            min_return=min_return,
            bb_window=bb_window if strategy_choice == "📊 布林通道策略" else 20,
            bb_std=bb_std if strategy_choice == "📊 布林通道策略" else 2.0,
            stop_loss_pct=stop_loss_pct if strategy_choice == "🚀 突破策略" else 6.0,
            take_profit_pct=take_profit_pct if strategy_choice == "🚀 突破策略" else 15.0,
            volume_threshold=volume_threshold if strategy_choice == "⚡ 日內交易策略 (CPR + Camarilla)" else 1.2
        )

def execute_batch_backtest(available_for_backtest, strategy_choice, period, initial_capital, min_return, 
                          bb_window=20, bb_std=2.0, stop_loss_pct=6.0, take_profit_pct=15.0, volume_threshold=1.2):
    """執行批量回測"""
    
    st.subheader("📊 批量回測進度")
    
    # 創建進度條
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    results = []
    successful_count = 0
    failed_count = 0
    
    for i, stock_code in enumerate(available_for_backtest):
        try:
            # 更新進度
            progress = (i + 1) / len(available_for_backtest)
            progress_bar.progress(progress)
            status_text.text(f"正在回測: {stock_code} ({i+1}/{len(available_for_backtest)})")
            
            # 獲取股價數據
            price_data = get_stock_price_data(stock_code, period)
            
            if price_data is None or len(price_data) < 60:
                failed_count += 1
                continue
            
            # 執行回測
            if strategy_choice == "📊 布林通道策略":
                backtest_result = bollinger_strategy_backtest(
                    price_data.copy(), 
                    initial_capital=initial_capital
                )
                strategy_name = "布林通道策略"
            
            elif strategy_choice == "🚀 突破策略":
                backtest_result = breakout_strategy_backtest(
                    price_data.copy(),
                    initial_capital=initial_capital,
                    stop_loss_pct=stop_loss_pct,
                    take_profit_pct=take_profit_pct
                )
                strategy_name = "突破策略"
            
            elif strategy_choice == "⚡ 日內交易策略 (CPR + Camarilla)":
                backtest_result = intraday_strategy_backtest(
                    price_data.copy(),
                    initial_capital=initial_capital,
                    volume_threshold=volume_threshold
                )
                strategy_name = "日內交易策略"
            
            elif strategy_choice == "🎯 多策略比較":
                # 執行三種策略
                bb_result = bollinger_strategy_backtest(price_data.copy(), initial_capital=initial_capital)
                breakout_result = breakout_strategy_backtest(
                    price_data.copy(), initial_capital=initial_capital,
                    stop_loss_pct=stop_loss_pct, take_profit_pct=take_profit_pct
                )
                intraday_result = intraday_strategy_backtest(
                    price_data.copy(), initial_capital=initial_capital,
                    volume_threshold=volume_threshold
                )
                
                # 添加三個結果
                if bb_result:
                    results.append({
                        '股票代碼': stock_code,
                        '策略': '布林通道策略',
                        '總報酬率(%)': round(bb_result['total_return'], 2),
                        '最終資金': int(bb_result['final_capital']),
                        '交易次數': len(bb_result['trades']),
                        '勝率(%)': calculate_win_rate(bb_result['trades'])
                    })
                
                if breakout_result:
                    results.append({
                        '股票代碼': stock_code,
                        '策略': '突破策略',
                        '總報酬率(%)': round(breakout_result['total_return'], 2),
                        '最終資金': int(breakout_result['final_capital']),
                        '交易次數': len(breakout_result['trades']),
                        '勝率(%)': calculate_win_rate(breakout_result['trades'])
                    })
                
                if intraday_result:
                    results.append({
                        '股票代碼': stock_code,
                        '策略': '日內交易策略',
                        '總報酬率(%)': round(intraday_result['total_return'], 2),
                        '最終資金': int(intraday_result['final_capital']),
                        '交易次數': len(intraday_result['trades']),
                        '勝率(%)': calculate_win_rate(intraday_result['trades'])
                    })
                
                successful_count += 1
                continue
            
            if backtest_result:
                results.append({
                    '股票代碼': stock_code,
                    '策略': strategy_name,
                    '總報酬率(%)': round(backtest_result['total_return'], 2),
                    '最終資金': int(backtest_result['final_capital']),
                    '交易次數': len(backtest_result['trades']),
                    '勝率(%)': calculate_win_rate(backtest_result['trades'])
                })
                successful_count += 1
            else:
                failed_count += 1
        
        except Exception as e:
            failed_count += 1
            continue
    
    # 完成回測
    progress_bar.progress(1.0)
    status_text.text(f"✅ 批量回測完成！成功: {successful_count}, 失敗: {failed_count}")
    
    if results:
        # 自動保存結果到CSV文件
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        results_df = pd.DataFrame(results)
        
        # 保存完整結果
        full_filename = f"online_backtest_full_{timestamp}.csv"
        results_df.to_csv(full_filename, index=False, encoding='utf-8-sig')
        
        # 篩選優質股票
        good_stocks = results_df[results_df['總報酬率(%)'] >= min_return]
        
        # 保存優質股票結果
        if len(good_stocks) > 0:
            profitable_filename = f"online_backtest_profitable_{min_return}pct_{timestamp}.csv"
            good_stocks.to_csv(profitable_filename, index=False, encoding='utf-8-sig')
            st.success(f"✅ 結果已自動保存到文件:")
            st.success(f"📁 完整結果: {full_filename}")
            st.success(f"📁 優質股票: {profitable_filename}")
        else:
            st.success(f"✅ 完整結果已保存到: {full_filename}")
        
        # 顯示結果
        st.subheader("📊 批量回測結果")
        
        # 顯示統計
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("總回測股票", len(results_df))
        with col2:
            st.metric(f"優質股票 (≥{min_return}%)", len(good_stocks))
        with col3:
            st.metric("平均報酬率", f"{results_df['總報酬率(%)'].mean():.2f}%")
        with col4:
            st.metric("最高報酬率", f"{results_df['總報酬率(%)'].max():.2f}%")
        
        # 顯示結果表格
        if len(good_stocks) > 0:
            st.subheader(f"🎯 優質股票清單 (報酬率 ≥ {min_return}%)")
            
            # 按報酬率排序
            good_stocks_sorted = good_stocks.sort_values('總報酬率(%)', ascending=False)
            st.dataframe(good_stocks_sorted, use_container_width=True)
            
            # 提供即時下載
            csv = good_stocks_sorted.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📥 下載優質股票清單 (即時)",
                data=csv,
                file_name=f"batch_backtest_results_{timestamp}.csv",
                mime="text/csv",
                key="download_current_results"
            )
        
        # 顯示完整結果
        with st.expander("📋 查看完整回測結果", expanded=False):
            results_sorted = results_df.sort_values('總報酬率(%)', ascending=False)
            st.dataframe(results_sorted, use_container_width=True)
            
            # 完整結果下載
            full_csv = results_sorted.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📥 下載完整回測結果",
                data=full_csv,
                file_name=f"full_backtest_results_{timestamp}.csv",
                mime="text/csv",
                key="download_full_results"
            )
        
        # 添加查看歷史結果的提示
        st.info("💡 您可以到「🎯 批量回測結果」頁面查看所有歷史回測結果")
    
    else:
        st.error("❌ 批量回測沒有產生任何有效結果")

def calculate_win_rate(trades):
    """計算勝率"""
    if not trades or len(trades) < 2:
        return 0
    
    profitable_trades = 0
    total_trades = 0
    
    for trade in trades:
        if 'Return' in trade and trade['Return'] is not None:
            total_trades += 1
            if trade['Return'] > 0:
                profitable_trades += 1
    
    return round((profitable_trades / total_trades * 100) if total_trades > 0 else 0, 1)

def show_batch_backtest(stock_data):
    """批量回測分頁"""
    st.subheader("🎯 批量回測結果查看")
    
    # 檢查是否有回測結果文件 - 擴展搜索範圍
    result_files = (glob.glob('backtest_results_*.csv') + 
                   glob.glob('multi_strategy_backtest_*.csv') + 
                   glob.glob('online_backtest_*.csv'))
    
    if not result_files:
        st.info("💡 尚未執行批量回測，請先執行批量回測來生成結果")
        show_batch_backtest_instructions()
        return
    
    # 顯示可用的回測結果文件
    st.subheader("📁 可用的回測結果文件")
    
    # 分類顯示不同類型的回測結果
    online_files = [f for f in result_files if 'online_backtest' in f]
    offline_files = [f for f in result_files if 'online_backtest' not in f]
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🌐 在線批量回測結果")
        if online_files:
            for file in sorted(online_files, key=os.path.getctime, reverse=True):
                file_info = os.path.basename(file)
                file_time = datetime.fromtimestamp(os.path.getctime(file)).strftime('%Y-%m-%d %H:%M:%S')
                if 'profitable' in file:
                    st.info(f"🎯 {file_info}\n📅 創建時間: {file_time}")
                else:
                    st.success(f"📊 {file_info}\n📅 創建時間: {file_time}")
        else:
            st.info("暫無在線批量回測結果")
    
    with col2:
        st.markdown("### 💻 離線批量回測結果")
        if offline_files:
            for file in sorted(offline_files, key=os.path.getctime, reverse=True):
                file_info = os.path.basename(file)
                file_time = datetime.fromtimestamp(os.path.getctime(file)).strftime('%Y-%m-%d %H:%M:%S')
                if 'profitable' in file:
                    st.info(f"🎯 {file_info}\n📅 創建時間: {file_time}")
                else:
                    st.success(f"📊 {file_info}\n📅 創建時間: {file_time}")
        else:
            st.info("暫無離線批量回測結果")
    
    # 文件選擇器
    st.subheader("🔍 選擇要查看的結果文件")
    
    # 創建文件選項
    file_options = {}
    for file in sorted(result_files, key=os.path.getctime, reverse=True):
        file_info = os.path.basename(file)
        file_time = datetime.fromtimestamp(os.path.getctime(file)).strftime('%Y-%m-%d %H:%M:%S')
        
        # 判斷文件類型
        if 'online_backtest' in file:
            source = "🌐 在線"
        else:
            source = "💻 離線"
        
        if 'profitable' in file:
            file_type = "🎯 優質股票"
        elif 'full' in file:
            file_type = "📊 完整結果"
        else:
            file_type = "📊 批量回測"
        
        display_name = f"{source} {file_type} - {file_time}"
        file_options[display_name] = file
    
    if file_options:
        selected_display = st.selectbox(
            "選擇結果文件:",
            list(file_options.keys()),
            help="選擇要查看的批量回測結果文件"
        )
        
        selected_file = file_options[selected_display]
        
        # 載入並顯示選中的結果
        try:
            display_backtest_results(selected_file)
        except Exception as e:
            st.error(f"❌ 載入結果文件失敗: {str(e)}")
    else:
        show_batch_backtest_instructions()

def display_backtest_results(file_path):
    """顯示批量回測結果"""
    try:
        df = pd.read_csv(file_path)
        file_name = os.path.basename(file_path)
        
        st.success(f"✅ 載入批量回測結果: {file_name}")
        
        # 檢測是否為多策略結果
        is_multi_strategy = '策略' in df.columns
        
        if is_multi_strategy:
            st.info("🎯 檢測到多策略回測結果，將顯示策略比較分析")
            display_multi_strategy_results(df)
        else:
            st.info("📊 單策略回測結果")
            display_single_strategy_results(df)
        
        # 顯示結果表格
        st.subheader("📋 詳細結果")
        
        # 按報酬率排序
        df_sorted = df.sort_values('總報酬率(%)', ascending=False)
        st.dataframe(df_sorted, use_container_width=True)
        
        # 提供下載功能
        csv = df_sorted.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="📥 下載此結果文件",
            data=csv,
            file_name=f"downloaded_{os.path.basename(file_path)}",
            mime="text/csv"
        )
        
        # 數據統計圖表
        if len(df) > 1:
            show_backtest_charts(df)
            
    except Exception as e:
        st.error(f"❌ 處理結果文件失敗: {str(e)}")

def display_multi_strategy_results(df):
    """顯示多策略回測結果"""
    strategies = df['策略'].unique()
    
    # 策略比較分析
    st.subheader("🔄 策略表現比較")
    
    strategy_stats = []
    for strategy in strategies:
        strategy_data = df[df['策略'] == strategy]
        profitable_count = len(strategy_data[strategy_data['總報酬率(%)'] >= 10])
        
        stats = {
            '策略': strategy,
            '測試股票數': len(strategy_data),
            '優質股票數': profitable_count,
            '成功率': f"{profitable_count/len(strategy_data)*100:.1f}%",
            '平均報酬率': f"{strategy_data['總報酬率(%)'].mean():.2f}%",
            '最高報酬率': f"{strategy_data['總報酬率(%)'].max():.2f}%",
            '平均勝率': f"{strategy_data['勝率(%)'].mean():.1f}%" if '勝率(%)' in strategy_data.columns else "N/A",
            '平均交易次數': f"{strategy_data['交易次數'].mean():.1f}" if '交易次數' in strategy_data.columns else "N/A"
        }
        strategy_stats.append(stats)
    
    strategy_comparison_df = pd.DataFrame(strategy_stats)
    st.dataframe(strategy_comparison_df, use_container_width=True)
    
    # 策略選擇器
    selected_strategy = st.selectbox(
        "選擇要分析的策略:",
        ["全部策略"] + list(strategies),
        help="選擇特定策略來查看詳細結果"
    )
    
    if selected_strategy != "全部策略":
        filtered_df = df[df['策略'] == selected_strategy].copy()
        st.info(f"📈 當前顯示: {selected_strategy} 的回測結果")
        return filtered_df
    
    return df

def display_single_strategy_results(df):
    """顯示單策略回測結果"""
    st.subheader("📊 回測統計總覽")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("總回測股票", len(df))
    
    with col2:
        profitable_count = len(df[df['總報酬率(%)'] >= 10])
        st.metric("優質股票 (≥10%)", profitable_count)
    
    with col3:
        avg_return = df['總報酬率(%)'].mean()
        st.metric("平均報酬率", f"{avg_return:.2f}%")
    
    with col4:
        max_return = df['總報酬率(%)'].max()
        st.metric("最高報酬率", f"{max_return:.2f}%")

def show_backtest_charts(df):
    """顯示回測結果圖表"""
    st.subheader("📈 數據視覺化")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 報酬率分布直方圖
        fig_hist = px.histogram(
            df, 
            x='總報酬率(%)', 
            nbins=20,
            title="報酬率分布",
            labels={'總報酬率(%)': '報酬率 (%)', 'count': '股票數量'}
        )
        fig_hist.update_layout(height=400)
        st.plotly_chart(fig_hist, use_container_width=True)
    
    with col2:
        # 勝率 vs 報酬率散點圖 (如果有勝率數據)
        if '勝率(%)' in df.columns:
            fig_scatter = px.scatter(
                df, 
                x='勝率(%)', 
                y='總報酬率(%)',
                title="勝率 vs 報酬率",
                labels={'勝率(%)': '勝率 (%)', '總報酬率(%)': '報酬率 (%)'}
            )
            fig_scatter.update_layout(height=400)
            st.plotly_chart(fig_scatter, use_container_width=True)
        else:
            # 交易次數 vs 報酬率散點圖
            if '交易次數' in df.columns:
                fig_scatter = px.scatter(
                    df, 
                    x='交易次數', 
                    y='總報酬率(%)',
                    title="交易次數 vs 報酬率",
                    labels={'交易次數': '交易次數', '總報酬率(%)': '報酬率 (%)'}
                )
                fig_scatter.update_layout(height=400)
                st.plotly_chart(fig_scatter, use_container_width=True)

def show_batch_backtest_instructions():
    """顯示批量回測說明"""
    st.markdown("### 🚀 如何執行批量回測")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🌐 在線批量回測 (推薦)")
        st.markdown("""
        1. 前往 **📊 個股策略回測** 頁面
        2. 選擇 **🎯 批量回測** 模式  
        3. 設定回測參數和範圍
        4. 點擊 **🚀 開始批量回測**
        5. 結果會自動保存並可在此查看
        
        **優點:**
        - 💻 在瀏覽器內直接執行
        - 📊 即時查看進度和結果
        - 💾 自動保存到CSV文件
        - 📈 支援多策略比較
        """)
    
    with col2:
        st.markdown("#### 💻 離線批量回測")
        st.markdown("""
        1. 執行批量回測腳本:
        ```bash
        python batch_backtest.py
        ```
        
        2. 或執行多策略比較:
        ```bash
        python multi_strategy_batch_backtest.py
        ```
        
        **優點:**
        - ⚡ 運行速度較快
        - 🔄 適合大批量處理
        - 📝 詳細的命令行輸出
        """)
    
    st.info("💡 建議先使用在線批量回測功能，操作更簡單直觀！")

# 股票篩選工具頁面
def show_stock_filter(stock_data):
    """股票篩選工具頁面"""
    st.markdown('<div class="page-header">🔍 股票篩選工具</div>', unsafe_allow_html=True)
    
    if stock_data is None:
        st.error("❌ 無法載入股票數據")
        return
    
    # 篩選條件設定
    st.subheader("📊 篩選條件設定")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📈 財務指標")
        
        # ROE 篩選
        roe_range = st.slider(
            "ROE (%)",
            min_value=0.0,
            max_value=50.0,
            value=(10.0, 30.0),
            step=0.5,
            help="股東權益報酬率"
        )
        
        # EPS 篩選
        eps_range = st.slider(
            "EPS (元)",
            min_value=0.0,
            max_value=20.0,
            value=(1.0, 10.0),
            step=0.1,
            help="每股盈餘"
        )
    
    with col2:
        st.markdown("### 📊 成長指標")
        
        # 年營收成長率篩選
        year_growth_range = st.slider(
            "年營收成長率 (%)",
            min_value=-50.0,
            max_value=100.0,
            value=(5.0, 50.0),
            step=1.0,
            help="年度營收成長率"
        )
        
        # 月營收成長率篩選
        month_growth_range = st.slider(
            "月營收成長率 (%)",
            min_value=-50.0,
            max_value=100.0,
            value=(0.0, 30.0),
            step=1.0,
            help="月度營收成長率"
        )
    
    # 快速預設策略
    st.subheader("⚡ 快速預設策略")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("💎 積極成長", help="ROE>20%, EPS>2, 年成長>30%, 月成長>30%"):
            roe_range = (20.0, 50.0)
            eps_range = (2.0, 20.0)
            year_growth_range = (30.0, 100.0)
            month_growth_range = (30.0, 100.0)
    
    with col2:
        if st.button("💰 價值投資", help="ROE>15%, EPS>1, 年成長>10%, 月成長>5%"):
            roe_range = (15.0, 50.0)
            eps_range = (1.0, 20.0)
            year_growth_range = (10.0, 100.0)
            month_growth_range = (5.0, 100.0)
    
    with col3:
        if st.button("🛡️ 保守投資", help="ROE>10%, EPS>0.5, 年成長>5%, 月成長>0%"):
            roe_range = (10.0, 50.0)
            eps_range = (0.5, 20.0)
            year_growth_range = (5.0, 100.0)
            month_growth_range = (0.0, 100.0)
    
    with col4:
        if st.button("🔥 高成長", help="ROE>5%, EPS>0, 年成長>50%, 月成長>40%"):
            roe_range = (5.0, 50.0)
            eps_range = (0.0, 20.0)
            year_growth_range = (50.0, 100.0)
            month_growth_range = (40.0, 100.0)
    
    # 執行篩選
    try:
        # 確保數據列存在
        required_columns = ['ROE', 'EPS']
        
        # 檢查並處理欄位名稱
        if 'ROE(%)' in stock_data.columns:
            stock_data['ROE'] = stock_data['ROE(%)']
        if '年營收成長率(%)' in stock_data.columns:
            stock_data['year_growth'] = stock_data['年營收成長率(%)']
        if '月營收成長率(%)' in stock_data.columns:
            stock_data['month_growth'] = stock_data['月營收成長率(%)']
        
        # 篩選數據
        filtered_data = stock_data[
            (stock_data['ROE'] >= roe_range[0]) & (stock_data['ROE'] <= roe_range[1]) &
            (stock_data['EPS'] >= eps_range[0]) & (stock_data['EPS'] <= eps_range[1])
        ]
        
        # 如果有成長率數據，進一步篩選
        if 'year_growth' in filtered_data.columns:
            filtered_data = filtered_data[
                (filtered_data['year_growth'] >= year_growth_range[0]) & 
                (filtered_data['year_growth'] <= year_growth_range[1])
            ]
        
        if 'month_growth' in filtered_data.columns:
            filtered_data = filtered_data[
                (filtered_data['month_growth'] >= month_growth_range[0]) & 
                (filtered_data['month_growth'] <= month_growth_range[1])
            ]
        
        # 顯示篩選結果
        st.subheader("📋 篩選結果")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("符合條件股票", len(filtered_data))
        with col2:
            st.metric("總股票數", len(stock_data))
        with col3:
            percentage = (len(filtered_data) / len(stock_data) * 100) if len(stock_data) > 0 else 0
            st.metric("篩選比例", f"{percentage:.1f}%")
        
        if len(filtered_data) > 0:
            # 顯示篩選結果表格
            st.dataframe(filtered_data.head(20), use_container_width=True)
            
            # 數據視覺化
            if len(filtered_data) > 1:
                st.subheader("📈 數據視覺化")
                
                # ROE vs EPS 散點圖
                fig = px.scatter(
                    filtered_data.head(50), 
                    x='ROE', 
                    y='EPS',
                    hover_data=['name'] if 'name' in filtered_data.columns else None,
                    title="ROE vs EPS 散點圖",
                    color_discrete_sequence=['#1f77b4']
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("⚠️ 沒有股票符合當前篩選條件，請放寬篩選標準")
            
    except Exception as e:
        st.error(f"❌ 篩選處理失敗: {str(e)}")
        st.info("💡 可能是數據格式問題，請檢查數據文件")

# 投資組合分析頁面
def show_portfolio_analysis(stock_data):
    """投資組合分析頁面"""
    st.markdown('<div class="page-header">📈 投資組合分析</div>', unsafe_allow_html=True)
    
    st.info("🚧 投資組合分析功能正在開發中...")
    
    if stock_data is not None:
        st.subheader("📊 可用股票概覽")
        
        # 顯示股票統計
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("總股票數", len(stock_data))
        with col2:
            avg_roe = stock_data['ROE'].mean() if 'ROE' in stock_data.columns else 0
            st.metric("平均ROE", f"{avg_roe:.2f}%")
        with col3:
            avg_eps = stock_data['EPS'].mean() if 'EPS' in stock_data.columns else 0
            st.metric("平均EPS", f"{avg_eps:.2f}")
        
        # 顯示前20支股票
        st.subheader("📋 股票清單")
        st.dataframe(stock_data.head(20), use_container_width=True)

# 計算日內交易指標 (CPR + Camarilla Pivot Points)
def calculate_intraday_indicators(df):
    """計算CPR和Camarilla樞軸點指標"""
    if df is None or len(df) < 2:
        return df
    
    df = df.copy()
    
    # 確保有必要的欄位
    required_columns = ['High', 'Low', 'Close', 'Volume']
    for col in required_columns:
        if col not in df.columns:
            st.error(f"❌ 缺少必要欄位: {col}")
            return df
    
    # 計算前一日的H、L、C
    df['Prev_High'] = df['High'].shift(1)
    df['Prev_Low'] = df['Low'].shift(1)
    df['Prev_Close'] = df['Close'].shift(1)
    
    # CPR 指標計算
    # 中樞 (Pivot Point)
    df['PP'] = (df['Prev_High'] + df['Prev_Low'] + df['Prev_Close']) / 3
    
    # CPR 上軌 (BC)
    df['BC'] = (df['Prev_High'] + df['Prev_Low']) / 2
    
    # CPR 下軌 (TC)
    df['TC'] = df['PP'] * 2 - df['BC']
    
    # Camarilla Pivot Points 計算
    range_hl = df['Prev_High'] - df['Prev_Low']
    
    # 阻力位 (H1-H4)
    df['H1'] = df['Prev_Close'] + (range_hl * 1.1 / 12)
    df['H2'] = df['Prev_Close'] + (range_hl * 1.1 / 6)
    df['H3'] = df['Prev_Close'] + (range_hl * 1.1 / 4)
    df['H4'] = df['Prev_Close'] + (range_hl * 1.1 / 2)
    
    # 支撐位 (L1-L4)
    df['L1'] = df['Prev_Close'] - (range_hl * 1.1 / 12)
    df['L2'] = df['Prev_Close'] - (range_hl * 1.1 / 6)
    df['L3'] = df['Prev_Close'] - (range_hl * 1.1 / 4)
    df['L4'] = df['Prev_Close'] - (range_hl * 1.1 / 2)
    
    # 計算平均成交量（用於量能判斷）
    df['Volume_MA10'] = df['Volume'].rolling(window=10).mean()
    
    return df

# 日內交易策略回測
def intraday_strategy_backtest(df, initial_capital=100000, volume_threshold=1.2):
    """CPR + Camarilla 日內交易策略回測"""
    if df is None or len(df) < 20:
        return None
    
    # 添加日內交易指標
    df = calculate_intraday_indicators(df)
    
    # 去除NaN值
    df = df.dropna().copy()
    
    if len(df) < 10:
        return None
    
    # 初始化變量
    position = 0  # 0: 無持股, 1: 做多, -1: 做空
    capital = initial_capital
    shares = 0
    trades = []
    entry_price = 0
    entry_signal = ""
    
    # 記錄每日資產價值
    portfolio_values = []
    
    for i in range(1, len(df)):
        current_row = df.iloc[i]
        prev_row = df.iloc[i-1]
        
        current_price = current_row['Close']
        current_high = current_row['High']
        current_low = current_row['Low']
        current_volume = current_row['Volume']
        
        # 獲取當日CPR和Camarilla指標
        pp = current_row['PP']
        bc = current_row['BC']  # CPR上軌
        tc = current_row['TC']  # CPR下軌
        
        h1, h2, h3, h4 = current_row['H1'], current_row['H2'], current_row['H3'], current_row['H4']
        l1, l2, l3, l4 = current_row['L1'], current_row['L2'], current_row['L3'], current_row['L4']
        
        volume_ma = current_row['Volume_MA10']
        
        # 跳過無效數據
        if pd.isna(pp) or pd.isna(bc) or pd.isna(tc):
            portfolio_values.append({
                'Date': current_row['Date'],
                'Portfolio_Value': capital,
                'Stock_Price': current_price
            })
            continue
        
        # 進場邏輯
        if position == 0:
            # 多方進場條件
            if (current_price > bc and  # 突破CPR上軌
                current_volume > volume_ma * volume_threshold and  # 放量突破
                current_high > h1):  # 站上第一阻力位
                
                # 做多進場
                shares = capital // current_price
                if shares > 0:
                    entry_price = current_price
                    capital -= shares * current_price
                    position = 1
                    entry_signal = "CPR突破+量能+H1站穩"
                    trades.append({
                        'Date': current_row['Date'],
                        'Action': 'BUY',
                        'Price': current_price,
                        'Shares': shares,
                        'Capital': capital,
                        'Signal': entry_signal,
                        'CPR_Level': f"BC:{bc:.2f}, PP:{pp:.2f}, TC:{tc:.2f}"
                    })
            
            # 空方進場條件
            elif (current_price < tc and  # 跌破CPR下軌
                  current_volume > volume_ma * volume_threshold and  # 放量跌破
                  current_low < l1):  # 跌破第一支撐位
                
                # 做空進場（模擬）
                shares = capital // current_price
                if shares > 0:
                    entry_price = current_price
                    capital -= shares * current_price
                    position = -1
                    entry_signal = "CPR跌破+量能+L1失守"
                    trades.append({
                        'Date': current_row['Date'],
                        'Action': 'SELL_SHORT',
                        'Price': current_price,
                        'Shares': shares,
                        'Capital': capital,
                        'Signal': entry_signal,
                        'CPR_Level': f"BC:{bc:.2f}, PP:{pp:.2f}, TC:{tc:.2f}"
                    })
        
        # 出場邏輯
        elif position != 0:
            exit_signal = ""
            should_exit = False
            
            if position == 1:  # 持多倉
                # 停利條件：觸及H3或H4
                if current_high >= h3:
                    should_exit = True
                    exit_signal = f"觸及H3停利 ({h3:.2f})"
                
                # 停損條件：跌回L1以下
                elif current_low <= l1:
                    should_exit = True
                    exit_signal = f"跌破L1停損 ({l1:.2f})"
                
                # CPR反向測試：拉回PP以下
                elif current_price < pp:
                    should_exit = True
                    exit_signal = f"跌破PP停損 ({pp:.2f})"
            
            elif position == -1:  # 持空倉
                # 停利條件：觸及L3或L4
                if current_low <= l3:
                    should_exit = True
                    exit_signal = f"觸及L3停利 ({l3:.2f})"
                
                # 停損條件：漲回H1以上
                elif current_high >= h1:
                    should_exit = True
                    exit_signal = f"突破H1停損 ({h1:.2f})"
                
                # CPR反向測試：反彈PP以上
                elif current_price > pp:
                    should_exit = True
                    exit_signal = f"突破PP停損 ({pp:.2f})"
            
            if should_exit:
                # 計算損益
                if position == 1:  # 多倉出場
                    capital += shares * current_price
                    return_pct = (current_price - entry_price) / entry_price * 100
                    action = 'SELL'
                elif position == -1:  # 空倉出場
                    profit = shares * (entry_price - current_price)
                    capital += shares * entry_price + profit
                    return_pct = (entry_price - current_price) / entry_price * 100
                    action = 'COVER'
                
                trades.append({
                    'Date': current_row['Date'],
                    'Action': action,
                    'Price': current_price,
                    'Shares': shares,
                    'Capital': capital,
                    'Signal': exit_signal,
                    'Return': return_pct
                })
                
                shares = 0
                position = 0
                entry_price = 0
        
        # 計算當前投資組合價值
        if position == 1:  # 持多倉
            portfolio_value = capital + shares * current_price
        elif position == -1:  # 持空倉
            portfolio_value = capital + shares * entry_price + shares * (entry_price - current_price)
        else:
            portfolio_value = capital
        
        portfolio_values.append({
            'Date': current_row['Date'],
            'Portfolio_Value': portfolio_value,
            'Stock_Price': current_price
        })
    
    # 如果最後還有持倉，強制平倉
    if position != 0:
        final_price = df.iloc[-1]['Close']
        if position == 1:
            capital += shares * final_price
            return_pct = (final_price - entry_price) / entry_price * 100
            action = 'SELL (Final)'
        else:
            profit = shares * (entry_price - final_price)
            capital += shares * entry_price + profit
            return_pct = (entry_price - final_price) / entry_price * 100
            action = 'COVER (Final)'
        
        trades.append({
            'Date': df.iloc[-1]['Date'],
            'Action': action,
            'Price': final_price,
            'Shares': shares,
            'Capital': capital,
            'Signal': 'Final Exit',
            'Return': return_pct
        })
    
    return {
        'final_capital': capital,
        'total_return': (capital - initial_capital) / initial_capital * 100,
        'trades': trades,
        'portfolio_values': pd.DataFrame(portfolio_values),
        'df_with_indicators': df
    }

# 主函數
def main():
    """主函數 - 頁面導航和內容顯示"""
    
    # 頁面標題
    st.markdown('<h1 class="main-header">📈 台灣股票分析平台</h1>', unsafe_allow_html=True)
    
    # 版本資訊
    st.markdown("""
    <div style="text-align: center; margin-bottom: 1rem;">
        <span style="background: linear-gradient(135deg, #1f77b4, #2e86ab); color: white; padding: 0.3rem 1rem; border-radius: 20px; font-size: 0.9rem; font-weight: bold;">
            🚀 版本 v3.4.0 - 雲端優化版
        </span>
    </div>
    """, unsafe_allow_html=True)
    
    # 最新更新提示
    with st.expander("🔥 v3.4.0 最新更新", expanded=False):
        st.markdown("""
        ### ✨ 雲端版本重大優化
        
        **🎯 核心改進:**
        - ✅ **完整示例數據**: 雲端版本現包含40支精選台灣股票
        - ✅ **智能數據回退**: 自動檢測數據質量，確保最佳用戶體驗
        - ✅ **模擬價格數據**: 為每支股票生成真實的OHLC歷史數據
        - ✅ **策略回測支援**: 所有策略在雲端版本都能正常運行
        
        **📊 數據規模:**
        - 股票篩選: 40支精選股票 (涵蓋各主要產業)
        - 價格數據: 支援1年、2年、3年、5年期間回測
        - 策略支援: 布林通道、突破策略、日內交易策略
        
        **🌐 雲端 vs 本地對比:**
        | 功能 | 雲端演示版 | 本地完整版 |
        |------|-----------|-----------|
        | 股票篩選 | ✅ 40支精選股票 | ✅ 767支完整股票 |
        | 個股回測 | ✅ 完整功能 | ✅ 632支股票數據 |
        | 批量回測 | ✅ 演示功能 | ✅ 完整批量分析 |
        | 投資組合 | ✅ 完整功能 | ✅ 完整功能 |
        
        **💡 使用提示:**
        - 雲端版本適合學習和演示
        - 本地版本提供完整的投資分析功能
        - 所有策略邏輯和計算方式完全相同
        """)
    
    st.markdown("---")
    
    # 載入股票數據
    stock_data = load_stock_data()
    
    # 側邊欄導航
    st.sidebar.markdown("## 🧭 功能導航")
    
    # 頁面選擇
    page = st.sidebar.selectbox(
        "選擇功能頁面",
        [
            "🔍 股票篩選工具",
            "📊 個股策略回測", 
            "🎯 批量回測",
            "📋 批量回測結果",
            "📈 投資組合分析"
        ]
    )
    
    # 根據選擇顯示對應頁面
    if page == "🔍 股票篩選工具":
        show_stock_filter(stock_data)
    
    elif page == "📊 個股策略回測":
        show_single_stock_backtest_page(stock_data)
    
    elif page == "🎯 批量回測":
        show_batch_backtest_page(stock_data)
    
    elif page == "📋 批量回測結果":
        show_batch_backtest(stock_data)
    
    elif page == "📈 投資組合分析":
        show_portfolio_analysis(stock_data)

# 顯示日內交易策略結果
def display_intraday_strategy_results(result, strategy_name):
    """顯示日內交易策略回測結果"""
    if not result:
        st.error("❌ 無回測結果可顯示")
        return
    
    st.success(f"✅ {strategy_name} 回測完成！")
    
    # 基本績效指標
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "總報酬率",
            f"{result['total_return']:.2f}%",
            delta=f"{result['total_return']:.2f}%"
        )
    
    with col2:
        st.metric(
            "最終資本",
            f"${result['final_capital']:,.0f}",
            delta=f"${result['final_capital'] - 100000:,.0f}"
        )
    
    with col3:
        trades_df = pd.DataFrame(result['trades'])
        total_trades = len(trades_df)
        st.metric("總交易次數", total_trades)
    
    with col4:
        if total_trades > 0:
            # 計算勝率
            profitable_trades = len(trades_df[trades_df.get('Return', 0) > 0])
            win_rate = profitable_trades / (total_trades // 2) * 100 if total_trades > 0 else 0
            st.metric("勝率", f"{win_rate:.1f}%")
        else:
            st.metric("勝率", "0%")
    
    # 投資組合價值走勢圖
    if 'portfolio_values' in result and not result['portfolio_values'].empty:
        st.subheader("📈 投資組合價值走勢")
        
        portfolio_df = result['portfolio_values'].copy()
        portfolio_df['Date'] = pd.to_datetime(portfolio_df['Date'])
        
        fig = go.Figure()
        
        # 投資組合價值
        fig.add_trace(go.Scatter(
            x=portfolio_df['Date'],
            y=portfolio_df['Portfolio_Value'],
            name='投資組合價值',
            line=dict(color='blue', width=2)
        ))
        
        # 股價走勢（标准化到相同起点）
        initial_portfolio = portfolio_df['Portfolio_Value'].iloc[0]
        initial_stock_price = portfolio_df['Stock_Price'].iloc[0]
        normalized_stock_price = portfolio_df['Stock_Price'] * (initial_portfolio / initial_stock_price)
        
        fig.add_trace(go.Scatter(
            x=portfolio_df['Date'],
            y=normalized_stock_price,
            name='股價走勢(標準化)',
            line=dict(color='gray', width=1, dash='dash')
        ))
        
        fig.update_layout(
            title="投資組合價值 vs 股價走勢",
            xaxis_title="日期",
            yaxis_title="價值 ($)",
            height=400,
            template="plotly_white"
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # CPR和Camarilla指標圖表
    if 'df_with_indicators' in result:
        st.subheader("📊 CPR & Camarilla 指標圖表")
        
        df_indicators = result['df_with_indicators'].copy()
        df_indicators['Date'] = pd.to_datetime(df_indicators['Date'])
        
        # 只显示最近60天的数据，避免图表过于拥挤
        recent_data = df_indicators.tail(60)
        
        fig = go.Figure()
        
        # 股价K线图
        fig.add_trace(go.Candlestick(
            x=recent_data['Date'],
            open=recent_data['Open'],
            high=recent_data['High'],
            low=recent_data['Low'],
            close=recent_data['Close'],
            name='股價K線',
            increasing_line_color='red',
            decreasing_line_color='green'
        ))
        
        # CPR指標線
        fig.add_trace(go.Scatter(
            x=recent_data['Date'], y=recent_data['BC'],
            name='CPR上軌(BC)', line=dict(color='orange', width=2)
        ))
        fig.add_trace(go.Scatter(
            x=recent_data['Date'], y=recent_data['PP'],
            name='CPR中樞(PP)', line=dict(color='purple', width=2)
        ))
        fig.add_trace(go.Scatter(
            x=recent_data['Date'], y=recent_data['TC'],
            name='CPR下軌(TC)', line=dict(color='brown', width=2)
        ))
        
        # Camarilla阻力位
        fig.add_trace(go.Scatter(
            x=recent_data['Date'], y=recent_data['H3'],
            name='H3阻力', line=dict(color='red', width=1, dash='dot')
        ))
        fig.add_trace(go.Scatter(
            x=recent_data['Date'], y=recent_data['H1'],
            name='H1阻力', line=dict(color='pink', width=1, dash='dot')
        ))
        
        # Camarilla支撐位
        fig.add_trace(go.Scatter(
            x=recent_data['Date'], y=recent_data['L1'],
            name='L1支撐', line=dict(color='lightblue', width=1, dash='dot')
        ))
        fig.add_trace(go.Scatter(
            x=recent_data['Date'], y=recent_data['L3'],
            name='L3支撐', line=dict(color='blue', width=1, dash='dot')
        ))
        
        # 標記交易點
        if len(trades_df) > 0:
            trades_df['Date'] = pd.to_datetime(trades_df['Date'])
            buy_trades = trades_df[trades_df['Action'].isin(['BUY', 'SELL_SHORT'])]
            sell_trades = trades_df[trades_df['Action'].isin(['SELL', 'COVER'])]
            
            if not buy_trades.empty:
                fig.add_trace(go.Scatter(
                    x=buy_trades['Date'],
                    y=buy_trades['Price'],
                    mode='markers',
                    marker=dict(symbol='triangle-up', size=10, color='green'),
                    name='進場點',
                    text=buy_trades['Signal'],
                    hovertemplate="<b>進場</b><br>日期: %{x}<br>價格: %{y}<br>信號: %{text}<extra></extra>"
                ))
            
            if not sell_trades.empty:
                fig.add_trace(go.Scatter(
                    x=sell_trades['Date'],
                    y=sell_trades['Price'],
                    mode='markers',
                    marker=dict(symbol='triangle-down', size=10, color='red'),
                    name='出場點',
                    text=sell_trades['Signal'],
                    hovertemplate="<b>出場</b><br>日期: %{x}<br>價格: %{y}<br>信號: %{text}<extra></extra>"
                ))
        
        fig.update_layout(
            title="CPR + Camarilla 日內交易指標圖 (最近60天)",
            xaxis_title="日期",
            yaxis_title="價格",
            height=600,
            template="plotly_white",
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # 交易明細
    if len(trades_df) > 0:
        st.subheader("📋 交易明細")
        
        # 格式化交易資料
        display_trades = trades_df.copy()
        display_trades['日期'] = pd.to_datetime(display_trades['Date']).dt.strftime('%Y-%m-%d')
        display_trades['動作'] = display_trades['Action'].map({
            'BUY': '🟢 買入',
            'SELL': '🔴 賣出',
            'SELL_SHORT': '🟠 賣空',
            'COVER': '🔵 回補',
            'SELL (Final)': '🔴 賣出(最終)',
            'COVER (Final)': '🔵 回補(最終)'
        })
        display_trades['價格'] = display_trades['Price'].round(2)
        display_trades['股數'] = display_trades['Shares']
        display_trades['信號'] = display_trades['Signal']
        
        if 'Return' in display_trades.columns:
            display_trades['報酬率(%)'] = display_trades['Return'].fillna(0).round(2)
        
        if 'CPR_Level' in display_trades.columns:
            display_trades['CPR水位'] = display_trades['CPR_Level']
        
        # 選擇要顯示的欄位
        display_columns = ['日期', '動作', '價格', '股數', '信號']
        if 'Return' in display_trades.columns:
            display_columns.append('報酬率(%)')
        if 'CPR_Level' in display_trades.columns:
            display_columns.append('CPR水位')
        
        st.dataframe(
            display_trades[display_columns],
            use_container_width=True,
            hide_index=True
        )
        
        # 交易統計
        if 'Return' in trades_df.columns:
            st.subheader("📊 交易統計")
            
            returns = trades_df['Return'].dropna()
            if len(returns) > 0:
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    avg_return = returns.mean()
                    st.metric("平均報酬率", f"{avg_return:.2f}%")
                
                with col2:
                    max_return = returns.max()
                    st.metric("最大單筆獲利", f"{max_return:.2f}%")
                
                with col3:
                    min_return = returns.min()
                    st.metric("最大單筆虧損", f"{min_return:.2f}%")
                
                with col4:
                    profitable_trades = len(returns[returns > 0])
                    total_completed_trades = len(returns)
                    win_rate = profitable_trades / total_completed_trades * 100 if total_completed_trades > 0 else 0
                    st.metric("實際勝率", f"{win_rate:.1f}%")
                
                # 報酬率分布圖
                fig = go.Figure(data=[go.Histogram(
                    x=returns,
                    nbinsx=20,
                    name='交易報酬率分布',
                    marker_color='lightblue',
                    opacity=0.7
                )])
                
                fig.update_layout(
                    title="交易報酬率分布",
                    xaxis_title="報酬率 (%)",
                    yaxis_title="交易次數",
                    height=300,
                    template="plotly_white"
                )
                
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("ℹ️ 該期間內無交易信號產生")
    
    # 策略分析總結
    st.subheader("📝 策略分析總結")
    
    summary_text = f"""
    **日內交易策略 (CPR + Camarilla Pivot Points) 回測結果：**
    
    📊 **績效表現：**
    - 總報酬率：{result['total_return']:.2f}%
    - 總交易次數：{total_trades}次
    - 最終資本：${result['final_capital']:,.0f}
    """
    
    if len(trades_df) > 0 and 'Return' in trades_df.columns:
        returns = trades_df['Return'].dropna()
        if len(returns) > 0:
            avg_return = returns.mean()
            win_rate = len(returns[returns > 0]) / len(returns) * 100
            summary_text += f"""
    - 平均單筆報酬：{avg_return:.2f}%
    - 交易勝率：{win_rate:.1f}%
            """
    
    summary_text += """
    
    📈 **策略特色：**
    - 結合CPR和Camarilla樞軸點的日內交易策略
    - 利用前日高低點計算當日支撐壓力位
    - 突破確認配合量能分析
    - 明確的停利停損機制
    
    ⚠️ **風險提醒：**
    - 日內交易需要密切監控盤面
    - 適合有經驗的短線交易者
    - 建議搭配資金管理使用
    """
    
    st.markdown(summary_text)

if __name__ == "__main__":
    main() 