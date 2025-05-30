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

# 獲取股票歷史價格
@st.cache_data
def get_stock_price_data(stock_code, period="1y"):
    """獲取股票歷史價格數據"""
    try:
        # 確保股票代碼格式正確
        if not stock_code.endswith('.TW'):
            stock_code = f"{stock_code}.TW"
        
        # 獲取股票數據
        ticker = yf.Ticker(stock_code)
        hist = ticker.history(period=period)
        
        if hist.empty:
            return None
        
        # 重置索引，將日期作為列
        hist.reset_index(inplace=True)
        return hist
    
    except Exception as e:
        st.error(f"獲取股價數據失敗: {str(e)}")
        return None

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
        ["🔍 股票篩選工具", "📊 個股策略回測", "📈 投資組合分析"],
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

def show_stock_screener(stock_data):
    """股票篩選工具頁面"""
    st.markdown('<div class="page-header">🔍 股票篩選工具</div>', unsafe_allow_html=True)
    
    if stock_data is None:
        st.error("❌ 無法載入股票數據，請確保數據文件存在")
        return
    
    # 篩選控制面板
    st.sidebar.markdown("### 📊 篩選條件設定")
    
    # ROE篩選
    roe_min = st.sidebar.slider(
        "ROE 最低標準 (%)",
        min_value=0.0,
        max_value=50.0,
        value=10.0,
        step=0.5
    )
    
    # EPS篩選
    eps_min = st.sidebar.slider(
        "EPS 最低標準",
        min_value=0.0,
        max_value=20.0,
        value=2.0,
        step=0.1
    )
    
    # 顯示篩選結果
    if st.sidebar.button("🔍 開始篩選", type="primary"):
        filtered_stocks = stock_data[
            (stock_data['ROE'] >= roe_min) & 
            (stock_data['EPS'] >= eps_min)
        ].copy()
        
        if len(filtered_stocks) > 0:
            st.success(f"✅ 找到 {len(filtered_stocks)} 支符合條件的股票")
            
            # 排序並顯示結果
            filtered_stocks = filtered_stocks.sort_values('ROE', ascending=False)
            
            # 顯示前20名
            st.subheader("🏆 篩選結果 (前20名)")
            display_cols = ['stock_code', 'name', 'ROE', 'EPS', '年營收成長率', '月營收成長率']
            available_cols = [col for col in display_cols if col in filtered_stocks.columns]
            
            st.dataframe(
                filtered_stocks[available_cols].head(20),
                use_container_width=True
            )
            
            # ROE vs EPS 散點圖
            fig = px.scatter(
                filtered_stocks.head(50),
                x='ROE',
                y='EPS',
                hover_data=['name'],
                title="ROE vs EPS 分布圖"
            )
            st.plotly_chart(fig, use_container_width=True)
            
        else:
            st.warning("⚠️ 沒有找到符合條件的股票，請調整篩選條件")

def show_strategy_backtest(stock_data):
    """個股策略回測頁面"""
    st.markdown('<div class="page-header">📊 個股策略回測</div>', unsafe_allow_html=True)
    
    # 股票代碼輸入
    col1, col2 = st.columns([2, 1])
    
    with col1:
        stock_input = st.text_input(
            "請輸入股票代碼 (例如: 2330, 2454, 0050)",
            value="2330",
            help="輸入台灣股票代碼，系統會自動添加.TW後綴"
        )
    
    with col2:
        period = st.selectbox(
            "選擇回測期間",
            ["1y", "2y", "3y", "5y"],
            index=0
        )
    
    if stock_input:
        # 獲取股票資訊
        stock_code = stock_input.strip()
        if stock_data is not None:
            stock_info = stock_data[stock_data['stock_code'].str.contains(stock_code, na=False)]
            if not stock_info.empty:
                stock_name = stock_info.iloc[0]['name']
                st.info(f"📈 選擇股票: {stock_code} - {stock_name}")
            else:
                st.warning(f"⚠️ 在數據庫中找不到股票 {stock_code} 的基本資料")
        
        # 獲取股價數據
        with st.spinner(f"正在獲取 {stock_code} 的股價數據..."):
            price_data = get_stock_price_data(stock_code, period)
        
        if price_data is not None:
            st.success(f"✅ 成功獲取 {len(price_data)} 天的股價數據")
            
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
                title=f"{stock_code} 股價走勢 ({period})",
                xaxis_title="日期",
                yaxis_title="股價 (TWD)",
                hovermode='x unified'
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # 策略設定
            st.subheader("🎯 布林通道策略設定")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                bb_window = st.number_input("移動平均週期", min_value=5, max_value=50, value=20)
            with col2:
                bb_std = st.number_input("標準差倍數", min_value=1.0, max_value=3.0, value=2.0, step=0.1)
            with col3:
                initial_capital = st.number_input("初始資金", min_value=10000, max_value=10000000, value=100000, step=10000)
            
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
                        title=f"{stock_code} 布林通道策略回測",
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
                
                else:
                    st.error("❌ 回測失敗，可能是數據不足或其他問題")
        else:
            st.error(f"❌ 無法獲取股票 {stock_code} 的價格數據，請檢查股票代碼是否正確")

def show_portfolio_analysis(stock_data):
    """投資組合分析頁面"""
    st.markdown('<div class="page-header">📈 投資組合分析</div>', unsafe_allow_html=True)
    st.info("🚧 此功能正在開發中，敬請期待！")
    
    if stock_data is not None:
        st.subheader("📊 可用於組合分析的股票數量")
        st.metric("股票總數", len(stock_data))

if __name__ == "__main__":
    main() 