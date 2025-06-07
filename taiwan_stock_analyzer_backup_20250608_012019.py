#!/usr/bin/env python3
"""
台灣股票分析平台 - 多頁面版本
包含：
1. 股票篩選工具
2. 個股策略回測
3. 投資組合分析
4. 批量回測結果
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

# 布林通道策略函數
def calculate_bollinger_bands(df, window=20, num_std=2):
    """計算布林通道"""
    if df is None or len(df) < window:
        return df
    
    df = df.copy()
    
    # 計算移動平均線
    df['SMA'] = df['Close'].rolling(window=window).mean()
    
    # 計算標準差
    df['STD'] = df['Close'].rolling(window=window).std()
    
    # 計算布林通道
    df['Upper_Band'] = df['SMA'] + (num_std * df['STD'])
    df['Lower_Band'] = df['SMA'] - (num_std * df['STD'])
    
    return df

def bollinger_strategy_backtest(df, initial_capital=100000):
    """布林通道策略回測"""
    if df is None or len(df) < 20:
        return None
    
    # 計算布林通道
    df = calculate_bollinger_bands(df)
    
    # 去除NaN值
    df = df.dropna().copy()
    
    if len(df) < 10:
        return None
    
    # 初始化變數
    position = 0  # 0: 空手, 1: 持股
    capital = initial_capital
    shares = 0
    trades = []
    
    # 記錄每日資產價值
    portfolio_values = []
    
    for i in range(1, len(df)):
        current_row = df.iloc[i]
        prev_row = df.iloc[i-1]
        
        current_price = current_row['Close']
        
        # 買入信號：價格從下方穿越下軌
        if (position == 0 and 
            prev_row['Close'] <= prev_row['Lower_Band'] and 
            current_price > current_row['Lower_Band']):
            
            # 買入
            shares = capital // current_price
            if shares > 0:
                capital -= shares * current_price
                position = 1
                trades.append({
                    'Date': current_row['Date'],
                    'Action': 'BUY',
                    'Price': current_price,
                    'Shares': shares,
                    'Capital': capital
                })
        
        # 賣出信號：價格從上方穿越上軌
        elif (position == 1 and 
              prev_row['Close'] <= prev_row['Upper_Band'] and 
              current_price > current_row['Upper_Band']):
            
            # 賣出
            capital += shares * current_price
            trades.append({
                'Date': current_row['Date'],
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
            'Date': current_row['Date'],
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

# 突破策略函數
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

# 統一回測結果顯示函數
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
        # 計算勝率
        trades_df = pd.DataFrame(backtest_result['trades'])
        if len(trades_df) > 0:
            sell_trades = trades_df[trades_df['Action'].str.contains('SELL')]
            if 'Return' in sell_trades.columns:
                winning_trades = len(sell_trades[sell_trades['Return'] > 0])
                total_trades = len(sell_trades)
                win_rate = winning_trades / total_trades * 100 if total_trades > 0 else 0
            else:
                win_rate = 0
        else:
            win_rate = 0
        
        st.metric(
            "勝率",
            f"{win_rate:.1f}%"
        )
    
    # 策略描述
    st.subheader(f"📈 {strategy_name} 策略說明")
    
    if strategy_name == "布林通道策略":
        st.info("""
        **布林通道策略邏輯:**
        - 📈 **買入信號**: 股價從下方突破布林通道下軌時買入
        - 📉 **賣出信號**: 股價從上方突破布林通道上軌時賣出
        - 🎯 **策略理念**: 利用價格均值回歸特性，在超跌時買入，超買時賣出
        """)
    
    elif strategy_name == "突破策略":
        st.info(f"""
        **突破策略邏輯:**
        - 🎯 **進場條件** (三個條件須同時滿足):
          1. 趨勢判斷：股價站上20日與60日均線
          2. 突破進場：當天收盤價 > 最近20日高點
          3. 成交量過濾：進場日成交量 > 前5日平均量
        
        - 🚪 **出場條件** (滿足任一條件即出場):
          1. 停損：收盤價跌破進場價-{stop_loss_pct}%即隔天出場
          2. 停利：達到+{take_profit_pct}%報酬即獲利了結
          3. 追蹤出場：跌破10日均線可分批減碼或出清
        """)
    
    # 交易記錄
    if len(backtest_result['trades']) > 0:
        st.subheader("📋 交易記錄")
        
        trades_df = pd.DataFrame(backtest_result['trades'])
        trades_df['Date'] = pd.to_datetime(trades_df['Date']).dt.strftime('%Y-%m-%d')
        
        # 格式化數值
        trades_df['Price'] = trades_df['Price'].round(2)
        trades_df['Capital'] = trades_df['Capital'].round(0)
        
        st.dataframe(trades_df, use_container_width=True)
        
        # 交易統計
        col1, col2, col3 = st.columns(3)
        
        with col1:
            total_trades = len(trades_df)
            st.metric("總交易次數", total_trades)
        
        with col2:
            buy_trades = len(trades_df[trades_df['Action'] == 'BUY'])
            st.metric("買入次數", buy_trades)
        
        with col3:
            sell_trades = len(trades_df[trades_df['Action'].str.contains('SELL')])
            st.metric("賣出次數", sell_trades)
    
    # 資產價值走勢圖
    if not backtest_result['portfolio_values'].empty:
        st.subheader("📈 資產價值走勢")
        
        portfolio_df = backtest_result['portfolio_values']
        
        # 創建雙軸圖表
        fig = go.Figure()
        
        # 添加投資組合價值
        fig.add_trace(go.Scatter(
            x=portfolio_df['Date'],
            y=portfolio_df['Portfolio_Value'],
            mode='lines',
            name='投資組合價值',
            line=dict(color='blue', width=2),
            yaxis='y'
        ))
        
        # 添加股價走勢
        fig.add_trace(go.Scatter(
            x=portfolio_df['Date'],
            y=portfolio_df['Stock_Price'],
            mode='lines',
            name='股價',
            line=dict(color='orange', width=1),
            yaxis='y2'
        ))
        
        # 標記買賣點
        if len(backtest_result['trades']) > 0:
            trades_df = pd.DataFrame(backtest_result['trades'])
            
            # 買入點
            buy_trades = trades_df[trades_df['Action'] == 'BUY']
            if len(buy_trades) > 0:
                fig.add_trace(go.Scatter(
                    x=buy_trades['Date'],
                    y=buy_trades['Price'],
                    mode='markers',
                    name='買入點',
                    marker=dict(color='green', size=10, symbol='triangle-up'),
                    yaxis='y2'
                ))
            
            # 賣出點
            sell_trades = trades_df[trades_df['Action'].str.contains('SELL')]
            if len(sell_trades) > 0:
                fig.add_trace(go.Scatter(
                    x=sell_trades['Date'],
                    y=sell_trades['Price'],
                    mode='markers',
                    name='賣出點',
                    marker=dict(color='red', size=10, symbol='triangle-down'),
                    yaxis='y2'
                ))
        
        # 設定雙軸
        fig.update_layout(
            title=f"{stock_code} - {strategy_name} 回測結果",
            xaxis_title="日期",
            yaxis=dict(
                title="投資組合價值 ($)",
                side="left",
                titlefont=dict(color="blue"),
                tickfont=dict(color="blue")
            ),
            yaxis2=dict(
                title="股價 ($)",
                side="right",
                overlaying="y",
                titlefont=dict(color="orange"),
                tickfont=dict(color="orange")
            ),
            legend=dict(x=0, y=1),
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # 技術指標圖表
    if 'df_with_indicators' in backtest_result:
        df_with_indicators = backtest_result['df_with_indicators']
        
        st.subheader("📊 技術指標圖表")
        
        fig = go.Figure()
        
        # 添加股價
        fig.add_trace(go.Scatter(
            x=df_with_indicators['Date'],
            y=df_with_indicators['Close'],
            mode='lines',
            name='股價',
            line=dict(color='black', width=2)
        ))
        
        # 根據策略添加不同的技術指標
        if strategy_name == "布林通道策略":
            # 添加布林通道
            fig.add_trace(go.Scatter(
                x=df_with_indicators['Date'],
                y=df_with_indicators['Upper_Band'],
                mode='lines',
                name='上軌',
                line=dict(color='red', dash='dash')
            ))
            
            fig.add_trace(go.Scatter(
                x=df_with_indicators['Date'],
                y=df_with_indicators['SMA'],
                mode='lines',
                name='中軌(均線)',
                line=dict(color='blue', dash='dash')
            ))
            
            fig.add_trace(go.Scatter(
                x=df_with_indicators['Date'],
                y=df_with_indicators['Lower_Band'],
                mode='lines',
                name='下軌',
                line=dict(color='green', dash='dash')
            ))
        
        elif strategy_name == "突破策略":
            # 添加移動平均線
            fig.add_trace(go.Scatter(
                x=df_with_indicators['Date'],
                y=df_with_indicators['MA10'],
                mode='lines',
                name='MA10',
                line=dict(color='red', dash='dash')
            ))
            
            fig.add_trace(go.Scatter(
                x=df_with_indicators['Date'],
                y=df_with_indicators['MA20'],
                mode='lines',
                name='MA20',
                line=dict(color='blue', dash='dash')
            ))
            
            fig.add_trace(go.Scatter(
                x=df_with_indicators['Date'],
                y=df_with_indicators['MA60'],
                mode='lines',
                name='MA60',
                line=dict(color='green', dash='dash')
            ))
        
        fig.update_layout(
            title=f"{stock_code} - 技術指標圖表",
            xaxis_title="日期",
            yaxis_title="價格 ($)",
            legend=dict(x=0, y=1),
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)

def show_stock_filter(stock_data):
    """股票篩選頁面"""
    st.markdown('<div class="page-header">🔍 智能股票篩選工具</div>', unsafe_allow_html=True)
    
    if stock_data is None:
        st.error("❌ 無法載入股票數據")
        return
    
    # 檢查並統一欄位名稱
    st.info("🔍 檢測到的數據欄位:")
    st.write(list(stock_data.columns))
    
    # 建立欄位映射
    column_mapping = {
        'ROE(%)': 'ROE',  # 實際數據中是 'ROE'
        'EPS': 'EPS',     # 這個相同
        '營收成長率(%)': '年營收成長率'  # 實際數據中是 '年營收成長率'
    }
    
    # 檢查必要欄位是否存在
    missing_columns = []
    for display_name, actual_name in column_mapping.items():
        if actual_name not in stock_data.columns:
            missing_columns.append(actual_name)
    
    if missing_columns:
        st.error(f"❌ 缺少必要的數據欄位: {missing_columns}")
        st.info("💡 可用的欄位包括:")
        for col in stock_data.columns:
            st.text(f"  - {col}")
        return
    
    # 顯示數據概覽
    st.subheader("📊 數據概覽")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("股票總數", len(stock_data))
    with col2:
        valid_roe = stock_data['ROE'].notna().sum()
        st.metric("有ROE數據", valid_roe)
    with col3:
        valid_eps = stock_data['EPS'].notna().sum()
        st.metric("有EPS數據", valid_eps)
    with col4:
        valid_revenue = stock_data['年營收成長率'].notna().sum()
        st.metric("有營收數據", valid_revenue)
    
    # 篩選條件設定
    st.subheader("🎛️ 篩選條件設定")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📈 獲利能力指標")
        
        # ROE篩選
        roe_min, roe_max = st.slider(
            "股東權益報酬率 ROE (%)",
            min_value=float(stock_data['ROE'].min()) if stock_data['ROE'].notna().any() else -50.0,
            max_value=float(stock_data['ROE'].max()) if stock_data['ROE'].notna().any() else 100.0,
            value=(5.0, 30.0),
            step=0.5,
            help="ROE越高表示公司運用股東資金的效率越好"
        )
        
        # EPS篩選
        eps_min, eps_max = st.slider(
            "每股盈餘 EPS (元)",
            min_value=float(stock_data['EPS'].min()) if stock_data['EPS'].notna().any() else -10.0,
            max_value=float(stock_data['EPS'].max()) if stock_data['EPS'].notna().any() else 50.0,
            value=(1.0, 20.0),
            step=0.1,
            help="EPS越高表示每股獲利越好"
        )
    
    with col2:
        st.markdown("### 🚀 成長性指標")
        
        # 營收成長率篩選
        revenue_growth_min, revenue_growth_max = st.slider(
            "年營收成長率 (%)",
            min_value=float(stock_data['年營收成長率'].min()) if stock_data['年營收成長率'].notna().any() else -50.0,
            max_value=float(stock_data['年營收成長率'].max()) if stock_data['年營收成長率'].notna().any() else 100.0,
            value=(0.0, 50.0),
            step=1.0,
            help="營收成長率越高表示公司成長越快"
        )
        
        # 市值篩選
        if 'market_cap' in stock_data.columns:
            # 將市值轉換為億元
            stock_data['市值_億元'] = stock_data['market_cap'] / 100000000
            market_cap_min, market_cap_max = st.slider(
                "市值 (億元)",
                min_value=float(stock_data['市值_億元'].min()) if stock_data['市值_億元'].notna().any() else 10.0,
                max_value=float(stock_data['市值_億元'].max()) if stock_data['市值_億元'].notna().any() else 10000.0,
                value=(50.0, 5000.0),
                step=10.0,
                help="市值篩選，避免過小或過大的公司"
            )
    
    # 快速預設策略
    st.subheader("⚡ 快速預設策略")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🚀 積極成長型", use_container_width=True):
            st.info("設定為: ROE>15%, EPS>3, 年營收成長>20%")
    
    with col2:
        if st.button("💰 價值投資型", use_container_width=True):
            st.info("設定為: ROE>10%, EPS>2, 穩健成長")
    
    with col3:
        if st.button("🛡️ 保守穩健型", use_container_width=True):
            st.info("設定為: ROE>8%, EPS>1, 低風險")
    
    # 執行篩選
    filtered_data = stock_data.copy()
    
    # 應用ROE篩選
    if stock_data['ROE'].notna().any():
        filtered_data = filtered_data[
            (filtered_data['ROE'] >= roe_min) & 
            (filtered_data['ROE'] <= roe_max)
        ]
    
    # 應用EPS篩選
    if stock_data['EPS'].notna().any():
        filtered_data = filtered_data[
            (filtered_data['EPS'] >= eps_min) & 
            (filtered_data['EPS'] <= eps_max)
        ]
    
    # 應用營收成長率篩選
    if stock_data['年營收成長率'].notna().any():
        filtered_data = filtered_data[
            (filtered_data['年營收成長率'] >= revenue_growth_min) & 
            (filtered_data['年營收成長率'] <= revenue_growth_max)
        ]
    
    # 應用市值篩選（如果有的話）
    if 'market_cap' in stock_data.columns:
        market_cap_min_raw = market_cap_min * 100000000
        market_cap_max_raw = market_cap_max * 100000000
        filtered_data = filtered_data[
            (filtered_data['market_cap'] >= market_cap_min_raw) & 
            (filtered_data['market_cap'] <= market_cap_max_raw)
        ]
    
    # 顯示篩選結果
    st.subheader(f"🎯 篩選結果 ({len(filtered_data)} 支股票)")
    
    if len(filtered_data) > 0:
        # 結果統計
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            avg_roe = filtered_data['ROE'].mean()
            st.metric("平均ROE", f"{avg_roe:.2f}%" if not pd.isna(avg_roe) else "N/A")
        
        with col2:
            avg_eps = filtered_data['EPS'].mean()
            st.metric("平均EPS", f"{avg_eps:.2f}" if not pd.isna(avg_eps) else "N/A")
        
        with col3:
            avg_revenue_growth = filtered_data['年營收成長率'].mean()
            st.metric("平均營收成長", f"{avg_revenue_growth:.2f}%" if not pd.isna(avg_revenue_growth) else "N/A")
        
        with col4:
            st.metric("篩選比例", f"{len(filtered_data)/len(stock_data)*100:.1f}%")
        
        # 顯示篩選結果表格
        display_columns = ['stock_code', 'name', 'ROE', 'EPS', '年營收成長率']
        if 'current_price' in filtered_data.columns:
            display_columns.append('current_price')
        if 'sector' in filtered_data.columns:
            display_columns.append('sector')
        
        # 確保所有顯示欄位都存在
        available_display_columns = [col for col in display_columns if col in filtered_data.columns]
        
        st.dataframe(
            filtered_data[available_display_columns].head(20),
            use_container_width=True
        )
        
        # 下載功能
        if st.download_button(
            label="📥 下載篩選結果",
            data=filtered_data.to_csv(index=False, encoding='utf-8-sig'),
            file_name=f"篩選股票_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        ):
            st.success("✅ 下載完成")
    
    else:
        st.warning("⚠️ 沒有股票符合您的篩選條件，請調整篩選參數")

def show_individual_backtest(stock_data):
    """個股回測分頁"""
    st.markdown('<div class="page-header">📊 個股策略回測</div>', unsafe_allow_html=True)
    
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
    
    # 創建兩欄布局
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # 股票選擇區域
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
        # 回測設定區域
        st.subheader("⚙️ 回測設定")
        
        # 回測期間選擇
        period = st.selectbox(
            "回測期間",
            ["1y", "2y", "3y", "5y"],
            index=0,
            help="選擇回測的時間範圍"
        )
        
        # 策略選擇
        strategy = st.selectbox(
            "選擇策略",
            ["布林通道策略", "突破策略"],
            help="選擇要使用的交易策略"
        )
        
        # 初始資金設定
        initial_capital = st.number_input(
            "初始資金 ($)",
            min_value=10000,
            max_value=10000000,
            value=100000,
            step=10000,
            help="設定回測的初始投資金額"
        )
    
    # 策略參數設定
    st.subheader("🎛️ 策略參數設定")
    
    if strategy == "布林通道策略":
        col1, col2 = st.columns(2)
        
        with col1:
            bb_window = st.slider(
                "移動平均週期",
                min_value=5,
                max_value=50,
                value=20,
                help="計算布林通道的移動平均週期"
            )
        
        with col2:
            bb_std = st.slider(
                "標準差倍數",
                min_value=1.0,
                max_value=3.0,
                value=2.0,
                step=0.1,
                help="布林通道的標準差倍數"
            )
        
        # 策略說明
        st.info("""
        **布林通道策略說明:**
        - 📈 當股價從下方突破下軌線時買入
        - 📉 當股價從上方突破上軌線時賣出
        - 🎯 利用價格回歸平均的特性進行交易
        """)
        
    elif strategy == "突破策略":
        col1, col2 = st.columns(2)
        
        with col1:
            stop_loss_pct = st.slider(
                "停損百分比 (%)",
                min_value=3.0,
                max_value=15.0,
                value=6.0,
                step=0.5,
                help="設定停損的百分比"
            )
        
        with col2:
            take_profit_pct = st.slider(
                "停利百分比 (%)",
                min_value=10.0,
                max_value=30.0,
                value=15.0,
                step=1.0,
                help="設定停利的百分比"
            )
        
        # 策略說明
        st.info(f"""
        **突破策略說明:**
        - 🎯 **進場條件**: 股價突破20日高點 + 站上均線 + 成交量放大
        - 📉 **停損**: 跌破進場價 -{stop_loss_pct}%
        - 📈 **停利**: 達到 +{take_profit_pct}% 報酬
        - 🔄 **追蹤出場**: 跌破10日均線
        """)
    
    # 執行回測按鈕
    if st.button("🚀 執行回測分析", type="primary", use_container_width=True):
        
        if not stock_input:
            st.error("❌ 請先選擇或輸入股票代碼")
            return
        
        with st.spinner(f"正在執行 {stock_input} 的 {strategy} 回測分析..."):
            
            # 載入股票數據
            price_data = get_stock_price_data(stock_input, period)
            
            if price_data is None:
                st.error(f"❌ 無法載入股票 {stock_input} 的價格數據")
                return
            
            # 獲取股票名稱
            stock_name = "未知"
            if stock_data is not None:
                stock_info = stock_data[stock_data['stock_code'].str.contains(stock_input, na=False)]
                if not stock_info.empty:
                    stock_name = stock_info.iloc[0]['name']
            
            # 執行回測
            backtest_result = None
            
            if strategy == "布林通道策略":
                # 設定布林通道參數並執行回測
                price_data_with_bb = calculate_bollinger_bands(price_data, window=bb_window, num_std=bb_std)
                backtest_result = bollinger_strategy_backtest(price_data_with_bb, initial_capital)
                
            elif strategy == "突破策略":
                # 執行突破策略回測
                backtest_result = breakout_strategy_backtest(
                    price_data, 
                    initial_capital=initial_capital,
                    stop_loss_pct=stop_loss_pct,
                    take_profit_pct=take_profit_pct
                )
            
            if backtest_result is None:
                st.error("❌ 回測執行失敗，可能是數據不足或其他錯誤")
                return
            
            # 顯示回測結果
            st.success(f"✅ {strategy} 回測完成！")
            
            # 使用統一的結果顯示UI
            if strategy == "布林通道策略":
                show_backtest_results_ui(
                    backtest_result, 
                    stock_input, 
                    stock_name, 
                    strategy, 
                    initial_capital
                )
            elif strategy == "突破策略":
                show_backtest_results_ui(
                    backtest_result, 
                    stock_input, 
                    stock_name, 
                    strategy, 
                    initial_capital,
                    stop_loss_pct=stop_loss_pct,
                    take_profit_pct=take_profit_pct
                )
            
            # 風險提醒
            st.subheader("⚠️ 風險提醒")
            st.warning("""
            **重要提醒:**
            - 📊 回測結果基於歷史數據，不保證未來表現
            - 💰 實際交易會有手續費、滑價等成本
            - 🎯 建議結合基本面分析進行投資決策
            - 📈 過去績效不代表未來投資收益
            - 🛡️ 投資有風險，請謹慎評估自身風險承受能力
            """)
    
    # 顯示數據庫統計（側邊欄樣式）
    with st.expander("📊 本地數據庫統計", expanded=False):
        if available_stocks:
            total_records = sum(stock['records'] for stock in available_stocks)
            avg_records = total_records // len(available_stocks)
            latest_update = max(stock['end_date'] for stock in available_stocks)
            oldest_data = min(stock['start_date'] for stock in available_stocks)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("可用股票數", len(available_stocks))
                st.metric("總交易記錄", f"{total_records:,}")
            
            with col2:
                st.metric("平均記錄數", f"{avg_records:,}")
                st.metric("資料涵蓋期間", f"{(latest_update - oldest_data).days} 天")
            
            with col3:
                st.metric("最新數據", latest_update.strftime('%Y-%m-%d'))
                st.metric("最舊數據", oldest_data.strftime('%Y-%m-%d'))
            
            # 前10支股票預覽
            st.markdown("### 📋 可用股票預覽 (前10支)")
            preview_data = []
            for stock in available_stocks[:10]:
                preview_data.append({
                    '股票代碼': stock['code'],
                    '記錄數': f"{stock['records']:,}",
                    '最新價格': f"{stock['latest_price']:.2f}",
                    '更新時間': stock['end_date'].strftime('%Y-%m-%d')
                })
            
            st.dataframe(pd.DataFrame(preview_data), use_container_width=True)

def show_portfolio_analysis(stock_data):
    """投資組合分析頁面"""
    st.markdown('<div class="page-header">📈 投資組合分析</div>', unsafe_allow_html=True)
    
    if stock_data is None:
        st.error("❌ 無法載入股票數據")
        return
    
    # 獲取可用股票列表
    available_stocks = get_available_stocks()
    
    if not available_stocks:
        st.error("❌ 本地數據庫中沒有可用的股票數據")
        st.info("💡 請先使用 TWSE 數據下載器下載股票數據")
        return
    
    st.success(f"✅ 本地數據庫已載入 {len(available_stocks)} 支股票的數據")
    
    # 使用session state來保存投資組合
    if 'portfolio_stocks' not in st.session_state:
        st.session_state.portfolio_stocks = []
    
    # 投資組合建立區域
    st.subheader("🎯 建立投資組合")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # 股票選擇
        stock_options = [f"{stock['code']}" for stock in available_stocks]
        selected_stock = st.selectbox(
            "選擇要加入組合的股票:",
            [""] + stock_options,
            help="從可用股票列表中選擇"
        )
        
        # 權重輸入
        weight = st.slider(
            "權重 (%)",
            min_value=1.0,
            max_value=100.0,
            value=10.0,
            step=1.0,
            help="設定此股票在投資組合中的權重"
        )
    
    with col2:
        st.markdown("### 📋 操作")
        
        # 添加股票到組合
        if st.button("➕ 添加到組合", use_container_width=True):
            if selected_stock and selected_stock != "":
                # 檢查股票是否已在組合中
                existing_stocks = [item['stock'] for item in st.session_state.portfolio_stocks]
                if selected_stock not in existing_stocks:
                    # 獲取股票名稱
                    stock_name = "未知"
                    if stock_data is not None:
                        stock_info = stock_data[stock_data['stock_code'].str.contains(selected_stock, na=False)]
                        if not stock_info.empty:
                            stock_name = stock_info.iloc[0]['name']
                    
                    st.session_state.portfolio_stocks.append({
                        'stock': selected_stock,
                        'name': stock_name,
                        'weight': weight
                    })
                    st.success(f"✅ 已添加 {selected_stock} - {stock_name}")
                    st.rerun()
                else:
                    st.warning(f"⚠️ {selected_stock} 已在投資組合中")
            else:
                st.warning("⚠️ 請先選擇股票")
        
        # 清空組合
        if st.button("🗑️ 清空組合", use_container_width=True):
            st.session_state.portfolio_stocks = []
            st.success("✅ 已清空投資組合")
            st.rerun()
    
    # 顯示當前投資組合
    if st.session_state.portfolio_stocks:
        st.subheader("📊 當前投資組合")
        
        # 計算總權重
        total_weight = sum(item['weight'] for item in st.session_state.portfolio_stocks)
        
        # 建立組合數據框
        portfolio_df = pd.DataFrame(st.session_state.portfolio_stocks)
        portfolio_df['normalized_weight'] = portfolio_df['weight'] / total_weight * 100
        
        # 顯示組合表格
        display_df = portfolio_df[['stock', 'name', 'weight', 'normalized_weight']].copy()
        display_df.columns = ['股票代碼', '股票名稱', '設定權重(%)', '正規化權重(%)']
        display_df['設定權重(%)'] = display_df['設定權重(%)'].round(1)
        display_df['正規化權重(%)'] = display_df['正規化權重(%)'].round(1)
        
        st.dataframe(display_df, use_container_width=True)
        
        # 權重統計
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("組合股票數", len(st.session_state.portfolio_stocks))
        with col2:
            st.metric("總權重", f"{total_weight:.1f}%")
        with col3:
            weight_status = "✅ 平衡" if abs(total_weight - 100) < 5 else "⚠️ 需調整"
            st.metric("權重狀態", weight_status)
        
        # 權重分布圓餅圖
        if len(st.session_state.portfolio_stocks) > 1:
            st.subheader("🥧 投資組合權重分布")
            
            fig_pie = px.pie(
                portfolio_df,
                values='normalized_weight',
                names='stock',
                title="投資組合權重分布",
                hover_data=['name']
            )
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_pie, use_container_width=True)
        
        # 簡化版投資組合分析
        if len(st.session_state.portfolio_stocks) >= 2:
            st.subheader("📈 快速投資組合分析")
            
            # 基本統計
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("投資組合多樣性", f"{len(st.session_state.portfolio_stocks)} 支股票")
            
            with col2:
                # 計算權重分散度
                weights = [item['weight'] for item in st.session_state.portfolio_stocks]
                weight_std = np.std(weights)
                diversification = "高" if weight_std < 5 else "中" if weight_std < 15 else "低"
                st.metric("權重分散度", diversification)
            
            with col3:
                # 計算行業分散度（基於股票數據）
                sectors = []
                for item in st.session_state.portfolio_stocks:
                    stock_code = item['stock']
                    stock_info = stock_data[stock_data['stock_code'].str.contains(stock_code, na=False)]
                    if not stock_info.empty and 'sector' in stock_info.columns:
                        sectors.append(stock_info.iloc[0]['sector'])
                    else:
                        sectors.append('未知')
                
                unique_sectors = len(set(sectors))
                st.metric("行業分散度", f"{unique_sectors} 個行業")
            
            # 投資建議
            st.subheader("💡 投資組合建議")
            
            if len(st.session_state.portfolio_stocks) < 5:
                st.info("💡 建議增加更多股票以提高分散效果，理想的投資組合包含5-10支不同行業的股票")
            
            if weight_std > 20:
                st.warning("⚠️ 權重分配不均，建議調整各股票權重以降低集中風險")
            
            if unique_sectors < 3:
                st.warning("⚠️ 行業集中度較高，建議選擇不同行業的股票以分散風險")
            
            # 完整分析選項
            st.markdown("---")
            st.info("🚀 **完整投資組合績效分析功能開發中！** 未來版本將包含:")
            st.markdown("""
            - 📊 歷史績效回測分析
            - 📈 風險收益指標計算
            - 🎯 夏普比率和最大回撤分析
            - 📋 個股貢獻度分析
            - 💰 資產配置優化建議
            """)
    
    else:
        st.info("💡 請先添加股票到投資組合中開始分析")
        
        # 投資組合建議
        st.subheader("📚 投資組合建立指南")
        
        with st.expander("💡 投資組合建立建議", expanded=True):
            st.markdown("""
            **建議的投資組合配置:**
            
            1. **分散投資原則**:
               - 選擇 5-10 支不同行業的股票
               - 避免單一股票權重超過 20%
               - 平衡成長股和價值股
            
            2. **行業分散建議**:
               - 科技股: 20-30%
               - 金融股: 15-25%
               - 傳統產業: 15-25%
               - 消費股: 10-20%
               - 其他: 10-20%
            
            3. **風險控制**:
               - 定期檢視和調整
               - 設定停損停利點
               - 避免過度集中
            """)
        
        # 推薦股票（基於篩選結果）
        if stock_data is not None and len(stock_data) > 0:
            st.subheader("🌟 推薦優質股票")
            
            # 簡單篩選優質股票
            quality_stocks = stock_data[
                (stock_data['ROE'] > 10) & 
                (stock_data['EPS'] > 1) & 
                (stock_data['年營收成長率'] > 5)
            ]
            
            if len(quality_stocks) > 0:
                st.success(f"✅ 基於 ROE>10%, EPS>1, 年營收成長>5% 篩選出 {len(quality_stocks)} 支優質股票")
                
                # 隨機選擇5支推薦
                sample_size = min(5, len(quality_stocks))
                recommended = quality_stocks.sample(n=sample_size)
                
                st.markdown("**推薦股票列表:**")
                for _, row in recommended.iterrows():
                    col1, col2, col3, col4 = st.columns([1, 2, 1, 1])
                    with col1:
                        st.code(row['stock_code'])
                    with col2:
                        st.text(row['name'])
                    with col3:
                        st.text(f"ROE: {row['ROE']:.1f}%")
                    with col4:
                        st.text(f"EPS: {row['EPS']:.2f}")
            else:
                st.info("💡 請使用股票篩選工具找到合適的投資標的")

def show_batch_backtest(stock_data):
    """批量回測分頁"""
    st.markdown('<div class="page-header">🎯 多策略批量回測結果</div>', unsafe_allow_html=True)
    
    # 檢查是否有回測結果文件
    result_files = glob.glob('backtest_results_*.csv') + glob.glob('multi_strategy_backtest_*.csv')
    
    if not result_files:
        st.info("💡 尚未執行批量回測，請先執行批量回測來生成結果")
        
        # 提供執行批量回測的選項
        st.markdown("### 🚀 執行批量回測")
        
        st.warning("⚠️ 請在命令行中執行相應的批量回測腳本來生成結果")
        
        with st.expander("📖 批量回測執行指南", expanded=True):
            st.markdown("""
            **執行批量回測的步驟:**
            
            1. **布林通道策略批量回測**:
            ```bash
            python batch_backtest.py
            ```
            
            2. **多策略批量回測**:
            ```bash
            python multi_strategy_batch_backtest.py
            ```
            
            **預期結果:**
            - 完整回測結果文件 (所有股票)
            - 篩選結果文件 (報酬率≥10%的股票)
            - 詳細分析報告
            """)
        
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
            unique_stocks = len(full_results['股票代碼'].unique()) if '股票代碼' in full_results.columns else len(full_results)
            st.metric("總回測股票", unique_stocks)
        
        with col2:
            if profitable_results is not None:
                profitable_count = len(profitable_results)
            else:
                profitable_count = len(full_results[full_results['總報酬率(%)'] >= 10])
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
        display_profitable = profitable_results if profitable_results is not None else full_results[full_results['總報酬率(%)'] >= 10].copy()
        
        if len(display_profitable) > 0:
            st.markdown(f"**找到 {len(display_profitable)} 支優質股票 (報酬率≥10%):**")
            display_df = display_profitable.sort_values('總報酬率(%)', ascending=False)
            st.dataframe(display_df.head(20), use_container_width=True)
        else:
            st.warning("⚠️ 沒有找到報酬率≥10%的股票")
        
        # 報酬率分布圖
        st.subheader("📊 報酬率分布分析")
        
        fig = px.histogram(
            full_results, 
            x='總報酬率(%)', 
            nbins=30,
            title="報酬率分布",
            labels={'總報酬率(%)': '報酬率 (%)', 'count': '股票數量'}
        )
        fig.add_vline(x=10, line_dash="dash", line_color="red", annotation_text="10%門檻")
        fig.add_vline(x=0, line_dash="dash", line_color="gray", annotation_text="損益平衡")
        st.plotly_chart(fig, use_container_width=True)
        
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

def main():
    """主函數"""
    # 載入股票數據
    stock_data = load_stock_data()
    
    # 主標題
    st.markdown('<div class="main-header">📈 台灣股票分析平台</div>', unsafe_allow_html=True)
    
    # 側邊欄導航
    st.sidebar.markdown("## 🧭 功能導航")
    
    page = st.sidebar.selectbox(
        "選擇功能頁面",
        [
            "🔍 智能股票篩選",
            "📊 個股策略回測", 
            "🎯 多策略批量回測",
            "📈 投資組合分析"
        ]
    )
    
    # 根據選擇顯示對應頁面
    if page == "🔍 智能股票篩選":
        show_stock_filter(stock_data)
    elif page == "📊 個股策略回測":
        show_individual_backtest(stock_data)
    elif page == "🎯 多策略批量回測":
        show_batch_backtest(stock_data)
    elif page == "📈 投資組合分析":
        show_portfolio_analysis(stock_data)
    
    # 側邊欄信息
    st.sidebar.markdown("---")
    st.sidebar.markdown("### ℹ️ 關於平台")
    st.sidebar.info("""
    **台灣股票分析平台 v3.2.1**
    
    🎯 **主要功能:**
    - 智能股票篩選
    - 布林通道策略回測
    - 突破策略回測
    - 投資組合分析
    
    📊 **數據來源:**
    - 台灣證券交易所 (TWSE)
    - 櫃買中心 (TPEx)
    
    ⚠️ **免責聲明:**
    本平台僅供學習和研究使用，
    不構成投資建議。
    """)

if __name__ == "__main__":
    main() 