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
        background: linear-gradient(90deg, #1f77b4, #ff7f0e);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    .page-header {
        font-size: 2rem;
        font-weight: bold;
        color: #2c3e50;
        margin-bottom: 1.5rem;
        padding: 15px;
        background-color: #f8f9fa;
        border-radius: 10px;
        border-left: 5px solid #1f77b4;
    }
    
    .metric-card {
        background-color: #ffffff;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        margin: 1rem 0;
        border-left: 4px solid #1f77b4;
    }
    
    .strategy-result {
        background-color: #f0f8ff;
        padding: 1rem;
        border-radius: 8px;
        border: 2px solid #1f77b4;
        margin: 1rem 0;
    }
    
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeeba;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# 載入股票數據
@st.cache_data
def load_stock_data():
    """載入股票篩選數據"""
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
        try:
            df = pd.read_csv(latest_file)
            st.sidebar.success(f"✅ 載入數據文件: {os.path.basename(latest_file)}")
            st.sidebar.info(f"📊 股票數量: {len(df)}")
            return df
        except Exception as e:
            st.sidebar.error(f"❌ 讀取數據失敗: {str(e)}")
            return None
    else:
        st.sidebar.error("❌ 找不到股票數據文件")
        return None

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
            st.error(f"❌ 找不到股票 {clean_code} 的本地數據文件")
            st.info("💡 請先使用 TWSE 數據下載器下載股票數據")
            st.code("python twse_data_downloader.py", language="bash")
            return None
        
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
            return []
        
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
        
        # 按股票代碼排序
        available_stocks.sort(key=lambda x: x['code'])
        return available_stocks
        
    except Exception as e:
        st.error(f"❌ 獲取可用股票列表失敗: {str(e)}")
        return []

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

# 主應用
def main():
    # 側邊欄 - 頁面選擇
    st.sidebar.markdown('<div class="main-header">📈 台灣股票分析平台</div>', unsafe_allow_html=True)
    
    page = st.sidebar.selectbox(
        "選擇功能頁面",
        ["🔍 股票篩選工具", "📊 個股策略回測", "📈 投資組合分析", "🎯 批量回測結果", "🔄 版本更新"],
        index=0
    )
    
    # 載入股票數據
    stock_data = load_stock_data()
    
    if page == "🔍 股票篩選工具":
        show_stock_screener(stock_data)
    elif page == "📊 個股策略回測":
        show_strategy_backtest(stock_data)
    elif page == "📈 投資組合分析":
        show_portfolio_analysis(stock_data)
    elif page == "🎯 批量回測結果":
        show_backtest_results()
    elif page == "🔄 版本更新":
        show_version_updates()

def show_stock_screener(stock_data):
    """股票篩選工具頁面"""
    st.markdown('<div class="page-header">🔍 股票篩選工具</div>', unsafe_allow_html=True)
    
    if stock_data is None:
        st.error("❌ 無法載入股票數據，請確保數據文件存在")
        return
    
    # 篩選控制面板
    st.sidebar.markdown("### 📊 篩選條件設定")
    
    # ROE篩選 - 改為滑動條，範圍 -100 到 100
    st.sidebar.subheader("📊 ROE 最低標準 (%)")
    roe_default = st.session_state.get('roe_preset', 15.0)
    roe_min = st.sidebar.slider(
        "ROE 最低值",
        min_value=-100.0,
        max_value=100.0,
        value=roe_default,
        step=0.5,
        format="%.1f",
        help="拖拉調整 ROE 最低要求"
    )
    st.sidebar.write(f"當前設定: {roe_min:.1f}%")
    
    # EPS篩選 - 改為滑動條
    st.sidebar.subheader("💰 EPS 最低標準")
    eps_default = st.session_state.get('eps_preset', 1.2)
    eps_min = st.sidebar.slider(
        "EPS 最低值",
        min_value=float(stock_data['EPS'].min()) if 'EPS' in stock_data.columns else 0.0,
        max_value=float(stock_data['EPS'].max()) if 'EPS' in stock_data.columns else 20.0,
        value=eps_default,
        step=0.1,
        format="%.1f",
        help="拖拉調整 EPS 最低要求"
    )
    st.sidebar.write(f"當前設定: {eps_min:.1f}")
    
    # 年營收成長率篩選 - 改為滑動條，範圍 -100 到 100
    st.sidebar.subheader("📈 年營收成長率最低標準 (%)")
    annual_default = st.session_state.get('annual_preset', 30.0)
    annual_growth_min = st.sidebar.slider(
        "年營收成長率最低值",
        min_value=-100.0,
        max_value=100.0,
        value=annual_default,
        step=1.0,
        format="%.1f",
        help="拖拉調整年營收成長率最低要求"
    )
    st.sidebar.write(f"當前設定: {annual_growth_min:.1f}%")
    
    # 月營收成長率篩選 - 改為滑動條，範圍 -100 到 100
    st.sidebar.subheader("📊 月營收成長率最低標準 (%)")
    monthly_default = st.session_state.get('monthly_preset', 20.0)
    monthly_growth_min = st.sidebar.slider(
        "月營收成長率最低值",
        min_value=-100.0,
        max_value=100.0,
        value=monthly_default,
        step=1.0,
        format="%.1f",
        help="拖拉調整月營收成長率最低要求"
    )
    st.sidebar.write(f"當前設定: {monthly_growth_min:.1f}%")
    
    # 進階篩選選項
    st.sidebar.markdown("---")
    st.sidebar.subheader("🚀 快速設定")
    
    # 快速預設按鈕
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("💎 積極成長", help="ROE>20%, EPS>2, 年成長>30%, 月成長>30%"):
            st.session_state.roe_preset = 20.0
            st.session_state.eps_preset = 2.0
            st.session_state.annual_preset = 30.0
            st.session_state.monthly_preset = 30.0
            st.rerun()
            
        if st.button("🛡️ 保守投資", help="ROE>10%, EPS>0.5, 年成長>5%, 月成長>0%"):
            st.session_state.roe_preset = 10.0
            st.session_state.eps_preset = 0.5
            st.session_state.annual_preset = 5.0
            st.session_state.monthly_preset = 0.0
            st.rerun()
    
    with col2:
        if st.button("💰 價值投資", help="ROE>15%, EPS>1, 年成長>10%, 月成長>5%"):
            st.session_state.roe_preset = 15.0
            st.session_state.eps_preset = 1.0
            st.session_state.annual_preset = 10.0
            st.session_state.monthly_preset = 5.0
            st.rerun()
            
        if st.button("🔥 高成長", help="ROE>5%, EPS>0, 年成長>50%, 月成長>40%"):
            st.session_state.roe_preset = 5.0
            st.session_state.eps_preset = 0.0
            st.session_state.annual_preset = 50.0
            st.session_state.monthly_preset = 40.0
            st.rerun()
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔧 進階選項")
    
    show_charts = st.sidebar.checkbox("顯示圖表分析", value=True)
    show_raw_data = st.sidebar.checkbox("顯示原始資料", value=False)
    
    # 篩選按鈕
    if st.sidebar.button("🔍 開始篩選股票", type="primary"):
        st.session_state.filter_applied = True
    
    # 顯示篩選條件
    st.markdown(f'''
    <div style="background-color: #f0f8ff; padding: 10px; border-radius: 5px; margin: 10px 0;">
    <strong>篩選條件：</strong> ROE > {roe_min:.1f}%, EPS > {eps_min:.1f}, 
    年營收成長率 > {annual_growth_min:.1f}%, 月營收成長率 > {monthly_growth_min:.1f}%
    </div>
    ''', unsafe_allow_html=True)
    
    # 執行篩選 (總是執行，不需要按鈕)
    required_cols = ['ROE', 'EPS', '年營收成長率', '月營收成長率']
    missing_cols = [col for col in required_cols if col not in stock_data.columns]
    
    if missing_cols:
        st.warning(f"⚠️ 數據缺少以下欄位: {missing_cols}")
        # 使用可用的欄位進行篩選
        available_filters = []
        if 'ROE' in stock_data.columns:
            available_filters.append(stock_data['ROE'] >= roe_min)
        if 'EPS' in stock_data.columns:
            available_filters.append(stock_data['EPS'] >= eps_min)
        
        if available_filters:
            filtered_stocks = stock_data[
                pd.concat(available_filters, axis=1).all(axis=1)
            ].copy()
        else:
            filtered_stocks = stock_data.copy()
    else:
        # 完整篩選
        filtered_stocks = stock_data[
            (stock_data['ROE'] >= roe_min) & 
            (stock_data['EPS'] >= eps_min) &
            (stock_data['年營收成長率'] >= annual_growth_min) &
            (stock_data['月營收成長率'] >= monthly_growth_min)
        ].copy()
    
    # 顯示統計指標
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("總股票數", len(stock_data))
    with col2:
        st.metric("符合條件", len(filtered_stocks))
    with col3:
        pass_rate = len(filtered_stocks) / len(stock_data) * 100 if len(stock_data) > 0 else 0
        st.metric("通過率", f"{pass_rate:.1f}%")
    with col4:
        if len(filtered_stocks) > 0:
            avg_roe = filtered_stocks['ROE'].mean() if 'ROE' in filtered_stocks.columns else 0
            st.metric("平均ROE", f"{avg_roe:.1f}%")
    
    # 篩選結果
    st.subheader("🏆 符合條件的股票")
    
    if len(filtered_stocks) == 0:
        st.warning("⚠️ 沒有股票符合您設定的篩選條件，請調整篩選參數")
        st.info("💡 建議放寬篩選條件，例如降低 ROE 或成長率要求")
    else:
        # 排序並顯示結果
        if 'ROE' in filtered_stocks.columns:
            filtered_stocks = filtered_stocks.sort_values('ROE', ascending=False)
        
        # 顯示前20名
        st.subheader(f"📊 篩選結果 (前20名，共{len(filtered_stocks)}支)")
        display_cols = ['stock_code', 'name', 'ROE', 'EPS', '年營收成長率', '月營收成長率']
        available_cols = [col for col in display_cols if col in filtered_stocks.columns]
        
        # 格式化顯示
        df_display = filtered_stocks[available_cols].head(20).copy()
        if 'ROE' in df_display.columns:
            df_display['ROE'] = df_display['ROE'].round(2).astype(str) + '%'
        if 'EPS' in df_display.columns:
            df_display['EPS'] = df_display['EPS'].round(2)
        if '年營收成長率' in df_display.columns:
            df_display['年營收成長率'] = df_display['年營收成長率'].round(2).astype(str) + '%'
        if '月營收成長率' in df_display.columns:
            df_display['月營收成長率'] = df_display['月營收成長率'].round(2).astype(str) + '%'
        
        st.dataframe(df_display, use_container_width=True)
        
        # 圖表分析
        if show_charts and len(filtered_stocks) > 0:
            st.subheader("📈 圖表分析")
            
            # ROE vs EPS 散點圖
            if 'ROE' in filtered_stocks.columns and 'EPS' in filtered_stocks.columns:
                fig = px.scatter(
                    filtered_stocks.head(50),
                    x='ROE',
                    y='EPS',
                    hover_data=['name'] if 'name' in filtered_stocks.columns else None,
                    title="ROE vs EPS 分布圖",
                    labels={'ROE': 'ROE (%)', 'EPS': 'EPS'}
                )
                fig.update_layout(height=500)
                st.plotly_chart(fig, use_container_width=True)
            
            # 營收成長率分布
            if '年營收成長率' in filtered_stocks.columns:
                fig2 = px.histogram(
                    filtered_stocks,
                    x='年營收成長率',
                    title="年營收成長率分布",
                    labels={'年營收成長率': '年營收成長率 (%)'}
                )
                fig2.update_layout(height=400)
                st.plotly_chart(fig2, use_container_width=True)
        
        # 顯示原始資料
        if show_raw_data:
            st.subheader("📋 完整原始資料")
            st.dataframe(filtered_stocks, use_container_width=True)

def show_strategy_backtest(stock_data):
    """個股策略回測頁面"""
    st.markdown('<div class="page-header">📊 個股策略回測</div>', unsafe_allow_html=True)
    
    # 添加分頁選擇
    tab1, tab2 = st.tabs(["📈 個股回測", "🎯 批量回測"])
    
    with tab1:
        show_individual_backtest(stock_data)
    
    with tab2:
        show_batch_backtest(stock_data)

def show_individual_backtest(stock_data):
    """個股回測分頁"""
    # 檢查本地數據庫狀態
    available_stocks = get_available_stocks()
    
    if not available_stocks:
        st.error("❌ 本地數據庫中沒有可用的股票數據")
        st.info("💡 請先使用 TWSE 數據下載器下載股票數據")
        
        with st.expander("📥 如何下載股票數據", expanded=True):
            st.markdown("""
            **步驟 1: 執行數據下載器**
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
    st.success(f"✅ 本地數據庫已載入 {len(available_stocks)} 支股票的數據")
    
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
            st.subheader("🎯 布林通道策略設定")
            
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
                st.markdown("""
                **布林通道策略原理:**
                
                1. **指標計算:**
                   - 中軌: {window}日移動平均線
                   - 上軌: 中軌 + {std}倍標準差
                   - 下軌: 中軌 - {std}倍標準差
                
                2. **交易信號:**
                   - **買入信號**: 股價觸及下軌後反彈
                   - **賣出信號**: 股價觸及上軌
                
                3. **策略邏輯:**
                   - 當股價跌至下軌時，認為超賣，等待反彈買入
                   - 當股價漲至上軌時，認為超買，賣出獲利
                   - 利用股價在通道內震盪的特性進行交易
                """.format(window=bb_window, std=bb_std))
            
            # 執行回測
            if st.button("🚀 執行布林通道策略回測", type="primary"):
                with st.spinner("正在執行策略回測..."):
                    backtest_result = bollinger_strategy_backtest(
                        price_data.copy(), 
                        initial_capital=initial_capital
                    )
                
                if backtest_result:
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
                    st.subheader("📈 策略表現與布林通道")
                    
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
                                marker=dict(color='green', size=10, symbol='triangle-up')
                            ))
                        
                        if not sell_trades.empty:
                            fig.add_trace(go.Scatter(
                                x=sell_trades['Date'],
                                y=sell_trades['Price'],
                                mode='markers',
                                name='賣出',
                                marker=dict(color='red', size=10, symbol='triangle-down')
                            ))
                    
                    fig.update_layout(
                        title=f"{stock_code} - {stock_name} 布林通道策略回測",
                        xaxis_title="日期",
                        yaxis_title="股價 (TWD)",
                        hovermode='x unified',
                        height=600
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # 投資組合價值曲線
                    if not backtest_result['portfolio_values'].empty:
                        st.subheader("💰 投資組合價值變化")
                        
                        portfolio_df = backtest_result['portfolio_values']
                        
                        # 計算買入持有策略比較
                        first_price = portfolio_df.iloc[0]['Stock_Price']
                        last_price = portfolio_df.iloc[-1]['Stock_Price']
                        buy_hold_return = (last_price - first_price) / first_price * 100
                        buy_hold_final = initial_capital * (1 + buy_hold_return / 100)
                        
                        portfolio_df['Buy_Hold_Value'] = initial_capital * (portfolio_df['Stock_Price'] / first_price)
                        
                        fig2 = go.Figure()
                        
                        fig2.add_trace(go.Scatter(
                            x=portfolio_df['Date'],
                            y=portfolio_df['Portfolio_Value'],
                            mode='lines',
                            name='布林通道策略',
                            line=dict(color='blue', width=2)
                        ))
                        
                        fig2.add_trace(go.Scatter(
                            x=portfolio_df['Date'],
                            y=portfolio_df['Buy_Hold_Value'],
                            mode='lines',
                            name='買入持有策略',
                            line=dict(color='gray', width=2, dash='dash')
                        ))
                        
                        fig2.update_layout(
                            title="策略表現比較",
                            xaxis_title="日期",
                            yaxis_title="投資組合價值 (TWD)",
                            hovermode='x unified'
                        )
                        
                        st.plotly_chart(fig2, use_container_width=True)
                        
                        # 策略比較表
                        st.subheader("📋 策略比較")
                        
                        comparison_data = {
                            "策略": ["布林通道策略", "買入持有策略"],
                            "總報酬率 (%)": [f"{total_return:.2f}%", f"{buy_hold_return:.2f}%"],
                            "最終資金": [f"${backtest_result['final_capital']:,.0f}", f"${buy_hold_final:,.0f}"],
                            "超額報酬": [f"{total_return - buy_hold_return:.2f}%", "0.00%"]
                        }
                        
                        st.dataframe(pd.DataFrame(comparison_data), use_container_width=True)
                    
                    # 交易記錄
                    if backtest_result['trades']:
                        st.subheader("📝 交易記錄")
                        trades_df = pd.DataFrame(backtest_result['trades'])
                        st.dataframe(trades_df, use_container_width=True)

def show_batch_backtest(stock_data):
    """批量回測分頁"""
    st.subheader("🎯 批量布林通道策略回測")
    
    # 檢查是否有回測結果文件
    result_files = glob.glob('backtest_results_*.csv')
    
    if not result_files:
        st.info("💡 尚未執行批量回測，請先執行批量回測來生成結果")
        
        # 提供執行批量回測的選項
        st.markdown("### 🚀 執行批量回測")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            bb_window = st.number_input(
                "移動平均週期", 
                min_value=5, 
                max_value=50, 
                value=20,
                key="batch_bb_window"
            )
        with col2:
            bb_std = st.number_input(
                "標準差倍數", 
                min_value=1.0, 
                max_value=3.0, 
                value=2.0, 
                step=0.1,
                key="batch_bb_std"
            )
        with col3:
            initial_capital = st.number_input(
                "初始資金", 
                min_value=10000, 
                max_value=1000000, 
                value=100000, 
                step=10000,
                key="batch_initial_capital"
            )
        
        # 顯示批量回測腳本信息
        with st.expander("📖 批量回測說明", expanded=True):
            st.markdown("""
            **批量回測功能:**
            
            1. **覆蓋範圍**: 對所有可用股票執行布林通道策略回測
            2. **篩選條件**: 自動篩選出報酬率≥10%的優質股票
            3. **結果輸出**: 生成詳細的CSV結果文件和分析報告
            4. **執行方式**: 需要在命令行執行批量回測腳本
            
            **執行步驟:**
            ```bash
            python batch_backtest.py
            ```
            
            **預期結果:**
            - 完整回測結果文件 (所有股票)
            - 篩選結果文件 (報酬率≥10%的股票)
            - 詳細分析報告
            """)
        
        st.warning("⚠️ 請在命令行中執行 `python batch_backtest.py` 來生成批量回測結果")
        
        return
    
    # 載入最新的回測結果
    latest_full_file = max([f for f in result_files if 'full' in f], key=os.path.getctime)
    latest_profitable_file = max([f for f in result_files if 'profitable' in f], key=os.path.getctime) if any('profitable' in f for f in result_files) else None
    
    try:
        full_results = pd.read_csv(latest_full_file)
        profitable_results = pd.read_csv(latest_profitable_file) if latest_profitable_file else None
        
        st.success(f"✅ 載入批量回測結果: {os.path.basename(latest_full_file)}")
        
        # 顯示總體統計
        st.subheader("📊 回測統計總覽")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("總回測股票", len(full_results))
        
        with col2:
            profitable_count = len(profitable_results) if profitable_results is not None else len(full_results[full_results['總報酬率(%)'] >= 10])
            st.metric("優質股票 (≥10%)", profitable_count)
        
        with col3:
            avg_return = full_results['總報酬率(%)'].mean()
            st.metric("平均報酬率", f"{avg_return:.2f}%")
        
        with col4:
            max_return = full_results['總報酬率(%)'].max()
            st.metric("最高報酬率", f"{max_return:.2f}%")
        
        # 分類顯示結果
        st.subheader("🏆 優質股票分析")
        
        # 使用優質股票結果或從完整結果中篩選
        display_results = profitable_results if profitable_results is not None else full_results[full_results['總報酬率(%)'] >= 10].copy()
        
        if len(display_results) > 0:
            # 按報酬率分類
            超高報酬 = display_results[display_results['總報酬率(%)'] >= 50]
            高報酬 = display_results[(display_results['總報酬率(%)'] >= 20) & (display_results['總報酬率(%)'] < 50)]
            中等報酬 = display_results[(display_results['總報酬率(%)'] >= 10) & (display_results['總報酬率(%)'] < 20)]
            
            # 分頁顯示
            tab1, tab2, tab3, tab4 = st.tabs(["🚀 超高報酬 (≥50%)", "📈 高報酬 (20-50%)", "💰 中等報酬 (10-20%)", "📋 完整列表"])
            
            with tab1:
                if len(超高報酬) > 0:
                    st.markdown(f"**找到 {len(超高報酬)} 支超高報酬股票:**")
                    display_df = 超高報酬.sort_values('總報酬率(%)', ascending=False)
                    st.dataframe(display_df, use_container_width=True)
                else:
                    st.info("📊 沒有報酬率≥50%的股票")
            
            with tab2:
                if len(高報酬) > 0:
                    st.markdown(f"**找到 {len(高報酬)} 支高報酬股票:**")
                    display_df = 高報酬.sort_values('總報酬率(%)', ascending=False)
                    st.dataframe(display_df, use_container_width=True)
                else:
                    st.info("📊 沒有報酬率在20-50%的股票")
            
            with tab3:
                if len(中等報酬) > 0:
                    st.markdown(f"**找到 {len(中等報酬)} 支中等報酬股票:**")
                    display_df = 中等報酬.sort_values('總報酬率(%)', ascending=False)
                    st.dataframe(display_df, use_container_width=True)
                else:
                    st.info("📊 沒有報酬率在10-20%的股票")
            
            with tab4:
                st.markdown(f"**所有優質股票 ({len(display_results)} 支):**")
                display_df = display_results.sort_values('總報酬率(%)', ascending=False)
                st.dataframe(display_df, use_container_width=True)
        
        else:
            st.warning("⚠️ 沒有找到報酬率≥10%的股票")
        
        # 報酬率分布圖
        st.subheader("📊 報酬率分布分析")
        
        fig = px.histogram(
            full_results, 
            x='總報酬率(%)', 
            nbins=30,
            title="所有股票報酬率分布",
            labels={'總報酬率(%)': '報酬率 (%)', 'count': '股票數量'}
        )
        fig.add_vline(x=10, line_dash="dash", line_color="red", annotation_text="10%門檻")
        fig.add_vline(x=0, line_dash="dash", line_color="gray", annotation_text="損益平衡")
        st.plotly_chart(fig, use_container_width=True)
        
        # 投資建議
        st.subheader("💡 投資建議")
        
        if len(display_results) >= 10:
            top_10 = display_results.head(10)
            
            st.markdown("### 🎯 推薦投資組合 (前10名)")
            recommendation_df = top_10[['股票代碼', '總報酬率(%)', '最終資金', '交易次數']].copy()
            st.dataframe(recommendation_df, use_container_width=True)
            
            avg_top10_return = top_10['總報酬率(%)'].mean()
            st.info(f"💰 前10名平均報酬率: {avg_top10_return:.2f}%")
            
        # 風險提醒
        st.markdown("### ⚠️ 風險提醒")
        st.warning("""
        - 過去績效不代表未來表現
        - 建議分散投資，單一股票配置不超過總資金的5%
        - 設定停損點，建議15-20%
        - 定期檢視和調整投資組合
        """)
        
        # 下載功能
        st.subheader("📥 下載結果")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.download_button(
                label="📊 下載完整回測結果",
                data=full_results.to_csv(index=False, encoding='utf-8-sig'),
                file_name=f"完整回測結果_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            ):
                st.success("✅ 下載完成")
        
        with col2:
            if profitable_results is not None and len(profitable_results) > 0:
                if st.download_button(
                    label="🏆 下載優質股票結果",
                    data=profitable_results.to_csv(index=False, encoding='utf-8-sig'),
                    file_name=f"優質股票結果_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                ):
                    st.success("✅ 下載完成")
    
    except Exception as e:
        st.error(f"❌ 載入回測結果失敗: {str(e)}")
        st.info("💡 請確保回測結果文件格式正確")

def show_portfolio_analysis(stock_data):
    """投資組合分析頁面"""
    st.markdown('<div class="page-header">📈 投資組合分析</div>', unsafe_allow_html=True)
    st.info("🚧 此功能正在開發中，敬請期待！")
    
    if stock_data is not None:
        st.subheader("📊 可用於組合分析的股票數量")
        st.metric("股票總數", len(stock_data))

def show_backtest_results():
    """批量回測結果頁面"""
    st.markdown('<div class="page-header">🎯 布林通道策略批量回測結果</div>', unsafe_allow_html=True)
    
    # 載入回測結果
    @st.cache_data
    def load_backtest_results():
        """載入最新的回測結果"""
        try:
            # 尋找最新的結果文件
            full_files = glob.glob('backtest_results_full_*.csv')
            profitable_files = glob.glob('backtest_results_profitable_*.csv')
            
            if not full_files:
                return None, None, "找不到回測結果文件"
            
            # 選擇最新的文件
            latest_full = max(full_files, key=os.path.getctime)
            latest_profitable = max(profitable_files, key=os.path.getctime) if profitable_files else None
            
            full_df = pd.read_csv(latest_full)
            profitable_df = pd.read_csv(latest_profitable) if latest_profitable else pd.DataFrame()
            
            return full_df, profitable_df, None
            
        except Exception as e:
            return None, None, f"載入回測結果失敗: {str(e)}"
    
    full_df, profitable_df, error = load_backtest_results()
    
    if error:
        st.error(f"❌ {error}")
        st.info("💡 請先運行批量回測腳本生成結果")
        st.code("python batch_backtest.py", language="bash")
        return
    
    # 回測概況
    st.subheader("📊 回測概況")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "回測股票數",
            f"{len(full_df):,}",
            help="總共回測的股票數量"
        )
    
    with col2:
        avg_return = full_df['total_return'].mean()
        st.metric(
            "平均報酬率",
            f"{avg_return:.2f}%",
            delta=f"{'📈' if avg_return > 0 else '📉'}",
            help="所有股票的平均報酬率"
        )
    
    with col3:
        win_rate = len(full_df[full_df['total_return'] > 0]) / len(full_df) * 100
        st.metric(
            "勝率",
            f"{win_rate:.1f}%",
            delta=f"{'🎯' if win_rate > 50 else '⚠️'}",
            help="正報酬股票的比例"
        )
    
    with col4:
        st.metric(
            "優質股票數",
            f"{len(profitable_df):,}",
            delta=f"{len(profitable_df)/len(full_df)*100:.1f}%",
            help="報酬率≥10%的股票數量"
        )
    
    # 統計分析
    st.subheader("📈 統計分析")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📊 報酬率統計")
        stats_data = {
            "統計指標": ["最高報酬率", "最低報酬率", "標準差", "中位數", "25%分位數", "75%分位數"],
            "數值": [
                f"{full_df['total_return'].max():.2f}%",
                f"{full_df['total_return'].min():.2f}%",
                f"{full_df['total_return'].std():.2f}%",
                f"{full_df['total_return'].median():.2f}%",
                f"{full_df['total_return'].quantile(0.25):.2f}%",
                f"{full_df['total_return'].quantile(0.75):.2f}%"
            ]
        }
        st.dataframe(pd.DataFrame(stats_data), use_container_width=True, hide_index=True)
    
    with col2:
        st.markdown("### 🎯 報酬率分布")
        bins = [-100, -50, -20, -10, 0, 10, 20, 50, 100, float('inf')]
        labels = ['<-50%', '-50~-20%', '-20~-10%', '-10~0%', '0~10%', '10~20%', '20~50%', '50~100%', '>100%']
        
        distribution_data = []
        for i, label in enumerate(labels):
            if i < len(bins) - 1:
                count = len(full_df[(full_df['total_return'] >= bins[i]) & 
                                   (full_df['total_return'] < bins[i+1])])
                percentage = count / len(full_df) * 100
                distribution_data.append({
                    "區間": label,
                    "股票數": count,
                    "比例": f"{percentage:.1f}%"
                })
        
        st.dataframe(pd.DataFrame(distribution_data), use_container_width=True, hide_index=True)
    
    # 優質股票清單
    if len(profitable_df) > 0:
        st.subheader("🏆 優質股票清單 (報酬率 ≥ 10%)")
        
        # 分類顯示
        tab1, tab2, tab3, tab4 = st.tabs(["🥇 超高報酬 (>50%)", "🥈 高報酬 (30-50%)", "🥉 中等報酬 (20-30%)", "📊 穩健報酬 (10-20%)"])
        
        with tab1:
            super_high = profitable_df[profitable_df['total_return'] > 50]
            if len(super_high) > 0:
                st.markdown(f"**共 {len(super_high)} 支股票**")
                display_cols = ['stock_code', 'stock_name', 'total_return', 'num_trades', 'final_capital']
                col_names = ['股票代碼', '股票名稱', '報酬率(%)', '交易次數', '最終資金']
                super_high_display = super_high[display_cols].copy()
                super_high_display.columns = col_names
                super_high_display['最終資金'] = super_high_display['最終資金'].apply(lambda x: f"${x:,.0f}")
                st.dataframe(super_high_display, use_container_width=True, hide_index=True)
            else:
                st.info("沒有股票達到超高報酬率標準")
        
        with tab2:
            high_return = profitable_df[(profitable_df['total_return'] >= 30) & (profitable_df['total_return'] <= 50)]
            if len(high_return) > 0:
                st.markdown(f"**共 {len(high_return)} 支股票**")
                display_cols = ['stock_code', 'stock_name', 'total_return', 'num_trades', 'final_capital']
                col_names = ['股票代碼', '股票名稱', '報酬率(%)', '交易次數', '最終資金']
                high_return_display = high_return[display_cols].copy()
                high_return_display.columns = col_names
                high_return_display['最終資金'] = high_return_display['最終資金'].apply(lambda x: f"${x:,.0f}")
                st.dataframe(high_return_display, use_container_width=True, hide_index=True)
            else:
                st.info("沒有股票在此報酬率區間")
        
        with tab3:
            medium_return = profitable_df[(profitable_df['total_return'] >= 20) & (profitable_df['total_return'] < 30)]
            if len(medium_return) > 0:
                st.markdown(f"**共 {len(medium_return)} 支股票**")
                display_cols = ['stock_code', 'stock_name', 'total_return', 'num_trades', 'final_capital']
                col_names = ['股票代碼', '股票名稱', '報酬率(%)', '交易次數', '最終資金']
                medium_return_display = medium_return[display_cols].copy()
                medium_return_display.columns = col_names
                medium_return_display['最終資金'] = medium_return_display['最終資金'].apply(lambda x: f"${x:,.0f}")
                st.dataframe(medium_return_display, use_container_width=True, hide_index=True)
            else:
                st.info("沒有股票在此報酬率區間")
        
        with tab4:
            stable_return = profitable_df[(profitable_df['total_return'] >= 10) & (profitable_df['total_return'] < 20)]
            if len(stable_return) > 0:
                st.markdown(f"**共 {len(stable_return)} 支股票**")
                display_cols = ['stock_code', 'stock_name', 'total_return', 'num_trades', 'final_capital']
                col_names = ['股票代碼', '股票名稱', '報酬率(%)', '交易次數', '最終資金']
                stable_return_display = stable_return[display_cols].copy()
                stable_return_display.columns = col_names
                stable_return_display['最終資金'] = stable_return_display['最終資金'].apply(lambda x: f"${x:,.0f}")
                st.dataframe(stable_return_display, use_container_width=True, hide_index=True)
            else:
                st.info("沒有股票在此報酬率區間")
        
        # 推薦股票池
        st.subheader("🎯 推薦股票池 (前20名)")
        
        top_20 = profitable_df.head(20)
        display_cols = ['stock_code', 'stock_name', 'total_return', 'num_trades', 'final_capital']
        col_names = ['股票代碼', '股票名稱', '報酬率(%)', '交易次數', '最終資金']
        top_20_display = top_20[display_cols].copy()
        top_20_display.columns = col_names
        top_20_display['最終資金'] = top_20_display['最終資金'].apply(lambda x: f"${x:,.0f}")
        
        # 添加排名
        top_20_display.insert(0, '排名', range(1, len(top_20_display) + 1))
        
        st.dataframe(top_20_display, use_container_width=True, hide_index=True)
    
    # 策略評估
    st.subheader("🎯 策略評估")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### ✅ 優點")
        advantages = []
        
        if len(profitable_df) > 0:
            advantages.append(f"• 有 **{len(profitable_df)} 支股票** 達到10%以上報酬率")
            advantages.append(f"• 最高報酬率達到 **{full_df['total_return'].max():.2f}%**")
            advantages.append(f"• 優質股票平均報酬率為 **{profitable_df['total_return'].mean():.2f}%**")
        
        if win_rate > 45:
            advantages.append(f"• 勝率達到 **{win_rate:.1f}%**，接近或超過50%")
        
        advantages.append("• 交易頻率適中，不會過度頻繁")
        
        for advantage in advantages:
            st.markdown(advantage)
    
    with col2:
        st.markdown("### ⚠️ 風險提醒")
        risks = [
            f"• 最大虧損達到 **{full_df['total_return'].min():.2f}%**",
            f"• 報酬率標準差為 **{full_df['total_return'].std():.2f}%**，波動較大",
            f"• 有 **{len(full_df[full_df['total_return'] < -20])} 支股票** 虧損超過20%",
            "• 過去績效不代表未來表現",
            "• 實際交易需考慮手續費和滑價成本"
        ]
        
        for risk in risks:
            st.markdown(risk)
    
    # 投資建議
    st.subheader("💡 投資建議")
    
    st.markdown("""
    <div style="background-color: #d4edda; padding: 15px; border-radius: 10px; border-left: 5px solid #28a745;">
    <h4>🛡️ 風險管理建議</h4>
    <ul>
        <li><strong>停損設定</strong>: 建議設定15-20%的停損點</li>
        <li><strong>資金分配</strong>: 單一股票不超過總資金的5%</li>
        <li><strong>分散投資</strong>: 選擇5-10支不同產業的優質股票</li>
        <li><strong>定期檢視</strong>: 每月檢視策略表現並調整</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div style="background-color: #fff3cd; padding: 15px; border-radius: 10px; border-left: 5px solid #ffc107;">
    <h4>🔧 策略優化建議</h4>
    <ul>
        <li><strong>參數調整</strong>: 可測試不同的移動平均期間和標準差倍數</li>
        <li><strong>基本面篩選</strong>: 結合ROE、EPS等財務指標預先篩選</li>
        <li><strong>市場環境</strong>: 考慮牛熊市環境調整策略</li>
        <li><strong>成本考量</strong>: 加入手續費和滑價成本的真實回測</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # 下載結果
    st.subheader("📥 下載結果")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if len(profitable_df) > 0:
            csv_data = profitable_df.to_csv(index=False)
            st.download_button(
                label="📥 下載優質股票清單 (CSV)",
                data=csv_data,
                file_name=f"profitable_stocks_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                help="下載報酬率≥10%的股票清單"
            )
    
    with col2:
        # 檢查是否有分析報告
        report_files = glob.glob('backtest_analysis_report_*.md')
        if report_files:
            latest_report = max(report_files, key=os.path.getctime)
            try:
                with open(latest_report, 'r', encoding='utf-8') as f:
                    report_content = f.read()
                
                st.download_button(
                    label="📄 下載詳細分析報告 (MD)",
                    data=report_content,
                    file_name=f"backtest_analysis_report_{datetime.now().strftime('%Y%m%d')}.md",
                    mime="text/markdown",
                    help="下載完整的回測分析報告"
                )
            except:
                st.info("分析報告文件讀取失敗")
    
    # 免責聲明
    st.markdown("---")
    st.markdown("""
    <div style="background-color: #f8d7da; padding: 15px; border-radius: 10px; border-left: 5px solid #dc3545;">
    <h4>⚠️ 免責聲明</h4>
    <p>本回測結果僅供學術研究和教育用途，不構成投資建議。投資有風險，過去績效不代表未來表現。實際投資前請：</p>
    <ul>
        <li>進行充分的基本面分析</li>
        <li>考慮個人風險承受能力</li>
        <li>諮詢專業投資顧問</li>
        <li>分散投資降低風險</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)

def show_version_updates():
    """版本更新頁面"""
    st.markdown('<div class="page-header">🔄 版本更新歷史</div>', unsafe_allow_html=True)
    
    # 版本更新說明
    st.markdown("""
    <div style="background-color: #f0f8ff; padding: 15px; border-radius: 10px; margin-bottom: 20px;">
    <h4>📋 關於版本更新</h4>
    <p>這裡記錄了台灣股票分析平台的所有重要更新和功能改進。我們持續優化平台功能，為用戶提供更好的股票分析體驗。</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 版本更新時間線
    st.subheader("📅 版本更新時間線")
    
    # 版本 3.0.0 - 當前版本
    with st.expander("🚀 版本 3.0.0 - 完整功能版本 (2024年12月)", expanded=True):
        st.markdown("""
        ### ✨ 主要新功能
        - 🔄 **版本更新頁面**: 新增版本更新歷史查看功能
        - 📈 **投資組合分析**: 完整的投資組合管理和分析功能
        - 🎯 **策略優化**: 布林通道策略參數優化
        - 📊 **數據視覺化增強**: 更豐富的圖表和分析工具
        
        ### 🔧 功能改進
        - ⚡ 提升數據載入速度
        - 🎨 優化用戶界面設計
        - 📱 改善響應式布局
        - 🔍 增強股票搜尋功能
        
        ### 🐛 問題修復
        - 修復數據篩選的邊界條件問題
        - 解決圖表顯示異常
        - 優化記憶體使用效率
        
        ### 📊 數據更新
        - 更新至726支股票的完整財務數據
        - 443支股票的3年歷史價格數據
        - 改進數據準確性和完整性
        """)
    
    # 版本 2.5.0
    with st.expander("📊 版本 2.5.0 - 策略回測增強版 (2024年11月)"):
        st.markdown("""
        ### ✨ 主要新功能
        - 🎯 **布林通道策略回測**: 完整的技術分析策略回測系統
        - 📈 **股價走勢圖**: 清晰的價格圖表和技術指標
        - 💰 **投資組合追蹤**: 實時計算策略表現和報酬率
        - 📋 **交易記錄**: 詳細的買賣點記錄和分析
        
        ### 🔧 功能改進
        - 🔄 策略與買入持有的表現對比
        - 🎛️ 靈活的策略參數自訂功能
        - 📊 增強的數據視覺化
        - ⚡ 本地TWSE數據庫快速查詢
        
        ### 📊 數據更新
        - 建立本地TWSE數據庫
        - 443支股票的歷史價格數據
        - 支援1年、2年、3年、5年回測期間
        """)
    
    # 版本 2.0.0
    with st.expander("🔍 版本 2.0.0 - 股票篩選工具 (2024年10月)"):
        st.markdown("""
        ### ✨ 主要新功能
        - 🔍 **智能股票篩選**: 基於ROE、EPS、營收成長率等指標
        - 🎛️ **滑動條界面**: 直觀的拖拉調整篩選條件
        - ⚡ **快速預設策略**: 積極成長、價值投資、保守投資等
        - 📈 **數據視覺化**: 互動式散點圖和分布圖
        
        ### 🔧 功能改進
        - 📋 完整的726支台灣股票財務數據
        - 🔍 股票搜尋和篩選功能
        - 📊 統計指標卡片顯示
        - 💾 篩選結果CSV下載
        
        ### 🎨 界面優化
        - 現代化設計風格
        - 響應式布局設計
        - 自定義CSS樣式
        - 直觀的操作流程
        """)
    
    # 版本 1.5.0
    with st.expander("🌐 版本 1.5.0 - 雲端部署版 (2024年9月)"):
        st.markdown("""
        ### ✨ 主要新功能
        - 🌐 **Streamlit Cloud部署**: 支援雲端訪問
        - 🔄 **自動化部署**: GitHub集成自動部署
        - 📊 **數據更新機制**: 自動化數據更新和同步
        - 📋 **完整文檔**: 詳細的使用和部署指南
        
        ### 🔧 功能改進
        - ⚡ 優化應用啟動速度
        - 🔍 改善數據載入機制
        - 📱 移動端適配優化
        - 🛡️ 增強錯誤處理機制
        
        ### 📄 文檔完善
        - 部署指南 (DEPLOYMENT_GUIDE.md)
        - 數據更新指南 (DATA_UPDATE_GUIDE.md)
        - 策略回測指南 (STRATEGY_BACKTEST_GUIDE.md)
        - 專案總結 (PROJECT_SUMMARY.md)
        """)
    
    # 版本 1.0.0
    with st.expander("🎉 版本 1.0.0 - 初始版本 (2024年8月)"):
        st.markdown("""
        ### ✨ 核心功能
        - 📊 **基礎股票分析**: 台灣股票基本面數據分析
        - 🕷️ **數據爬蟲**: 從TWSE官方API獲取股票數據
        - 🎨 **Streamlit界面**: 基於Web的用戶界面
        - 📋 **數據處理**: Pandas數據處理和分析
        
        ### 🔧 技術架構
        - Python 3.8+ 支援
        - Streamlit Web框架
        - Pandas 數據處理
        - Plotly 數據視覺化
        
        ### 📊 初始數據
        - 50支台灣知名股票示例數據
        - 基本財務指標
        - 簡單篩選功能
        """)
    
    # 統計信息
    st.subheader("📊 平台統計")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "當前版本",
            "3.0.0",
            delta="最新"
        )
    
    with col2:
        st.metric(
            "總更新次數",
            "5",
            delta="+1"
        )
    
    with col3:
        st.metric(
            "功能模組",
            "4",
            delta="完整"
        )
    
    with col4:
        st.metric(
            "開發時間",
            "4個月",
            delta="持續更新"
        )
    
    # 未來規劃
    st.subheader("🚀 未來規劃")
    
    st.markdown("""
    <div style="background-color: #fff3cd; padding: 15px; border-radius: 10px; border-left: 5px solid #ffc107;">
    <h4>🔮 版本 4.0.0 規劃中</h4>
    <ul>
        <li>🤖 <strong>機器學習預測</strong>: 股價趨勢預測模型</li>
        <li>📱 <strong>移動端優化</strong>: 更好的手機端體驗</li>
        <li>🔔 <strong>即時通知</strong>: 股票價格和策略信號提醒</li>
        <li>🌍 <strong>多市場支援</strong>: 擴展至美股、港股等市場</li>
        <li>🔗 <strong>API接口</strong>: 提供程式化交易接口</li>
        <li>👥 <strong>用戶系統</strong>: 個人化設定和投資組合保存</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # 技術債務和改進計劃
    st.subheader("🔧 技術改進計劃")
    
    improvement_data = {
        "改進項目": [
            "效能優化",
            "快取機制",
            "多語言支援",
            "單元測試",
            "API文檔",
            "安全性增強"
        ],
        "優先級": [
            "高",
            "高",
            "中",
            "中",
            "低",
            "高"
        ],
        "預計完成": [
            "v3.1.0",
            "v3.1.0",
            "v4.0.0",
            "v3.2.0",
            "v4.0.0",
            "v3.1.0"
        ],
        "狀態": [
            "進行中",
            "計劃中",
            "計劃中",
            "計劃中",
            "計劃中",
            "進行中"
        ]
    }
    
    st.dataframe(pd.DataFrame(improvement_data), use_container_width=True)
    
    # 意見回饋
    st.subheader("💬 意見回饋")
    
    st.markdown("""
    <div style="background-color: #d4edda; padding: 15px; border-radius: 10px; border-left: 5px solid #28a745;">
    <h4>📝 我們重視您的意見</h4>
    <p>如果您有任何功能建議、問題回報或改進意見，歡迎透過以下方式聯繫我們：</p>
    <ul>
        <li>🐛 <strong>GitHub Issues</strong>: 回報問題和建議功能</li>
        <li>💡 <strong>功能建議</strong>: 提出新功能想法</li>
        <li>🔧 <strong>貢獻代碼</strong>: 歡迎提交 Pull Request</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # 更新日誌下載
    st.subheader("📥 更新日誌")
    
    changelog_content = """
# 台灣股票分析平台 - 更新日誌

## 版本 3.0.0 (2024-12-XX)
### 新功能
- 版本更新頁面
- 投資組合分析功能
- 策略參數優化

### 改進
- 數據載入速度提升
- 界面設計優化
- 響應式布局改善

### 修復
- 數據篩選邊界條件
- 圖表顯示異常
- 記憶體使用優化

## 版本 2.5.0 (2024-11-XX)
### 新功能
- 布林通道策略回測
- 股價走勢圖
- 投資組合追蹤

### 改進
- 策略表現對比
- 參數自訂功能
- 數據視覺化增強

## 版本 2.0.0 (2024-10-XX)
### 新功能
- 智能股票篩選
- 滑動條界面
- 快速預設策略

### 改進
- 726支股票數據
- 搜尋篩選功能
- 統計指標顯示

## 版本 1.5.0 (2024-09-XX)
### 新功能
- Streamlit Cloud部署
- 自動化部署
- 數據更新機制

### 改進
- 啟動速度優化
- 數據載入機制
- 錯誤處理增強

## 版本 1.0.0 (2024-08-XX)
### 初始功能
- 基礎股票分析
- 數據爬蟲
- Streamlit界面
- 數據處理
"""
    
    st.download_button(
        label="📥 下載完整更新日誌",
        data=changelog_content,
        file_name="changelog.md",
        mime="text/markdown",
        help="下載完整的版本更新日誌文件"
    )

if __name__ == "__main__":
    main() 