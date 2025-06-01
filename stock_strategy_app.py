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
            name=strategy_name,
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
            "策略": [strategy_name, "買入持有策略"],
            "總報酬率 (%)": [f"{total_return:.2f}%", f"{buy_hold_return:.2f}%"],
            "最終資金": [f"${backtest_result['final_capital']:,.0f}", f"${buy_hold_final:,.0f}"],
            "超額報酬": [f"{total_return - buy_hold_return:.2f}%", "0.00%"]
        }
        
        # 如果是突破策略，添加風險參數資訊
        if strategy_name == "突破策略" and stop_loss_pct and take_profit_pct:
            st.info(f"🎯 策略參數: 停損 -{stop_loss_pct}% | 停利 +{take_profit_pct}%")
        
        st.dataframe(pd.DataFrame(comparison_data), use_container_width=True)
    
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
            st.subheader("🎯 交易策略選擇")
            
            # 策略選擇
            strategy_choice = st.radio(
                "選擇回測策略:",
                ["📊 布林通道策略", "🚀 突破策略"],
                horizontal=True,
                help="選擇要使用的交易策略"
            )
            
            if strategy_choice == "📊 布林通道策略":
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
            
            elif strategy_choice == "🚀 突破策略":
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

def show_batch_backtest(stock_data):
    """批量回測分頁"""
    st.subheader("🎯 多策略批量回測結果")
    
    # 檢查是否有回測結果文件
    result_files = glob.glob('backtest_results_*.csv') + glob.glob('multi_strategy_backtest_*.csv')
    
    if not result_files:
        st.info("💡 尚未執行批量回測，請先執行批量回測來生成結果")
        
        # 提供執行批量回測的選項
        st.markdown("### 🚀 執行批量回測")
        
        # 策略選擇
        strategy_type = st.radio(
            "選擇回測模式:",
            ["📊 單一策略 (布林通道)", "🎯 多策略比較 (布林通道 + 突破策略)"],
            horizontal=True
        )
        
        if strategy_type == "📊 單一策略 (布林通道)":
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
            with st.expander("📖 布林通道批量回測說明", expanded=True):
                st.markdown("""
                **布林通道批量回測功能:**
                
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
                
        else:  # 多策略比較
            col1, col2, col3 = st.columns(3)
            with col1:
                stop_loss_pct = st.number_input(
                    "突破策略停損 (%)", 
                    min_value=1.0, 
                    max_value=20.0, 
                    value=6.0,
                    step=0.5,
                    key="multi_stop_loss"
                )
            with col2:
                take_profit_pct = st.number_input(
                    "突破策略停利 (%)", 
                    min_value=5.0, 
                    max_value=50.0, 
                    value=15.0, 
                    step=1.0,
                    key="multi_take_profit"
                )
            with col3:
                initial_capital = st.number_input(
                    "初始資金", 
                    min_value=10000, 
                    max_value=1000000, 
                    value=100000, 
                    step=10000,
                    key="multi_initial_capital"
                )
            
            # 多策略回測說明
            with st.expander("📖 多策略批量回測說明", expanded=True):
                st.markdown(f"""
                **多策略批量回測功能:**
                
                1. **同時測試兩種策略**:
                   - 📊 **布林通道策略**: 利用超買超賣信號
                   - 🚀 **突破策略**: 趨勢跟隨 + 量價配合 (停損{stop_loss_pct}%, 停利{take_profit_pct}%)
                
                2. **比較分析**:
                   - 各策略的成功率比較
                   - 平均報酬率對比
                   - 勝率和風險分析
                   - 適合股票類型分析
                
                3. **執行方式**:
                ```bash
                python multi_strategy_batch_backtest.py
                ```
                
                **預期結果:**
                - 包含兩種策略的完整回測結果
                - 策略表現比較分析
                - 各策略的優質股票推薦
                - 詳細統計數據 (勝率、平均報酬等)
                """)
        
        st.warning("⚠️ 請在命令行中執行相應的批量回測腳本來生成結果")
        
        return
    
    # 載入最新的回測結果
    latest_full_file = max([f for f in result_files if 'full' in f], key=os.path.getctime)
    latest_profitable_file = max([f for f in result_files if 'profitable' in f], key=os.path.getctime) if any('profitable' in f for f in result_files) else None
    
    try:
        full_results = pd.read_csv(latest_full_file)
        profitable_results = pd.read_csv(latest_profitable_file) if latest_profitable_file else None
        
        st.success(f"✅ 載入批量回測結果: {os.path.basename(latest_full_file)}")
        
        # 檢測是否為多策略結果
        is_multi_strategy = '策略' in full_results.columns
        
        if is_multi_strategy:
            st.info("🎯 檢測到多策略回測結果，將顯示策略比較分析")
            
            # 策略比較分析
            st.subheader("🔄 策略表現比較")
            
            strategies = full_results['策略'].unique()
            strategy_stats = []
            
            for strategy in strategies:
                strategy_data = full_results[full_results['策略'] == strategy]
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
            
            # 策略選擇器來篩選顯示
            st.subheader("📊 分策略分析")
            
            selected_strategy = st.selectbox(
                "選擇要分析的策略:",
                ["全部策略"] + list(strategies),
                help="選擇特定策略來查看詳細結果"
            )
            
            if selected_strategy != "全部策略":
                display_results = full_results[full_results['策略'] == selected_strategy].copy()
                profitable_results = display_results[display_results['總報酬率(%)'] >= 10].copy() if len(display_results) > 0 else None
                st.info(f"📈 當前顯示: {selected_strategy} 的回測結果")
            else:
                display_results = full_results
        else:
            display_results = full_results
        
        # 顯示總體統計
        st.subheader("📊 回測統計總覽")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if is_multi_strategy and selected_strategy != "全部策略":
                st.metric("當前策略測試股票", len(display_results))
            else:
                unique_stocks = len(display_results['股票代碼'].unique()) if '股票代碼' in display_results.columns else len(display_results)
                st.metric("總回測股票", unique_stocks)
        
        with col2:
            if profitable_results is not None:
                profitable_count = len(profitable_results)
            else:
                profitable_count = len(display_results[display_results['總報酬率(%)'] >= 10])
            st.metric("優質股票 (≥10%)", profitable_count)
        
        with col3:
            avg_return = display_results['總報酬率(%)'].mean()
            st.metric("平均報酬率", f"{avg_return:.2f}%")
        
        with col4:
            max_return = display_results['總報酬率(%)'].max()
            st.metric("最高報酬率", f"{max_return:.2f}%")
        
        # 分類顯示結果
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