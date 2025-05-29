import streamlit as st
import pandas as pd
import glob
import os
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# 設定頁面配置
st.set_page_config(
    page_title="台灣股票篩選工具",
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
    
    .filter-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #2c3e50;
        margin-bottom: 1rem;
        padding: 10px;
        background-color: #f8f9fa;
        border-radius: 5px;
        border-left: 4px solid #1f77b4;
    }
    
    .metric-card {
        background-color: #ffffff;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 0.5rem 0;
        border-left: 4px solid #1f77b4;
    }
    
    .result-header {
        font-size: 1.8rem;
        font-weight: bold;
        color: #27ae60;
        margin: 2rem 0 1rem 0;
        text-align: center;
    }
    
    .criteria-text {
        font-size: 1.2rem;
        color: #34495e;
        text-align: center;
        margin-bottom: 2rem;
        padding: 15px;
        background-color: #ecf0f1;
        border-radius: 8px;
        border: 1px solid #bdc3c7;
    }
    
    .tab-style {
        background-color: #f8f9fa;
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 10px;
    }
    
    /* 滑動條樣式優化 */
    .stSlider > div > div > div > div {
        background-color: #1f77b4;
    }
    
    /* 側邊欄按鈕樣式 */
    .stButton > button {
        width: 100%;
        border-radius: 8px;
        border: 1px solid #ddd;
        padding: 0.5rem;
        font-size: 0.8rem;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        background-color: #1f77b4;
        color: white;
        border-color: #1f77b4;
        box-shadow: 0 2px 4px rgba(31, 119, 180, 0.3);
    }
    
    /* 當前設定值顯示樣式 */
    .sidebar .stWrite {
        background-color: #f8f9fa;
        border-radius: 4px;
        padding: 4px 8px;
        font-size: 0.9rem;
        font-weight: bold;
        color: #1f77b4;
        border-left: 3px solid #1f77b4;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_stock_data():
    """載入最新的股票數據"""
    # 優先搜索修正後的數據文件
    search_patterns = [
        'data/processed/fixed_real_stock_data_*.csv',  # 修正版數據（最優先）
        'data/processed/hybrid_real_stock_data_*.csv',
        'data/processed/taiwan_all_stocks_complete_*.csv',
        'data/processed/stock_data_*.csv',
        'data/processed/taiwan_*.csv',
        'fixed_real_stock_data_*.csv',  # 當前目錄的修正版數據
        'hybrid_real_stock_data_*.csv',
        'stock_data_*.csv',
        'taiwan_*.csv'
    ]
    
    all_files = []
    for pattern in search_patterns:
        files = glob.glob(pattern)
        all_files.extend(files)
    
    if not all_files:
        return None, "找不到任何股票資料檔案"
    
    # 優先選擇修正版數據文件，然後按文件大小排序
    fixed_files = [f for f in all_files if 'fixed_real_stock_data' in f]
    
    if fixed_files:
        # 如果有修正版數據，選擇最新的
        latest_file = max(fixed_files, key=os.path.getctime)
    else:
        # 否則按文件大小選擇最大的文件
        file_sizes = []
        for file in all_files:
            try:
                size = os.path.getsize(file)
                file_sizes.append((file, size))
            except:
                continue
        
        if not file_sizes:
            return None, "無法讀取數據文件大小"
        
        # 按文件大小排序，選擇最大的文件
        file_sizes.sort(key=lambda x: x[1], reverse=True)
        latest_file = file_sizes[0][0]
        
        # 如果最大文件太小（小於10KB），則按時間選擇最新文件
        if file_sizes[0][1] < 10000:
            latest_file = max(all_files, key=os.path.getctime)
    
    try:
        df = pd.read_csv(latest_file)
        
        # 檢查並處理列名的變化
        column_mapping = {
            'stock_code': ['stock_code', '股票代號', 'code'],
            'name': ['name', '股票名稱', 'company_name'],
            'ROE': ['ROE', 'roe'],
            'EPS': ['EPS', 'eps'],
            '年營收成長率': ['年營收成長率', 'annual_growth', '年成長率'],
            '月營收成長率': ['月營收成長率', 'monthly_growth', '月成長率']
        }
        
        # 重新映射列名
        for standard_name, possible_names in column_mapping.items():
            for possible_name in possible_names:
                if possible_name in df.columns:
                    if possible_name != standard_name:
                        df = df.rename(columns={possible_name: standard_name})
                    break
        
        # 確保必要的欄位存在
        required_columns = ['stock_code', 'name', 'ROE', 'EPS', '年營收成長率', '月營收成長率']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            return None, f"缺少關鍵欄位: {missing_columns}"
        
        # 清理數據
        for col in ['ROE', 'EPS', '年營收成長率', '月營收成長率']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # 移除包含NaN的行
        df = df.dropna(subset=['ROE', 'EPS'])
        
        # 添加文件信息到返回結果
        file_size_mb = os.path.getsize(latest_file) / (1024 * 1024)
        
        # 檢查是否是修正版數據
        if 'fixed_real_stock_data' in latest_file:
            data_quality = "✅ 修正版真實數據"
        else:
            data_quality = "⚠️ 原始數據"
        
        file_info_with_size = f"{latest_file} ({file_size_mb:.1f}MB, {len(df)} stocks) - {data_quality}"
        
        return df, file_info_with_size
    
    except Exception as e:
        return None, f"載入數據時發生錯誤: {str(e)}"

def display_metrics(df_filtered, df_original):
    """顯示統計指標"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric(
            label="📊 符合條件股票數",
            value=len(df_filtered),
            delta=f"{len(df_filtered) - len(df_original)} (總數: {len(df_original)})"
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        avg_roe = df_filtered['ROE'].mean() if not df_filtered.empty else 0
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric(
            label="📈 平均ROE (%)",
            value=f"{avg_roe:.2f}%"
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        avg_eps = df_filtered['EPS'].mean() if not df_filtered.empty else 0
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric(
            label="💰 平均EPS",
            value=f"{avg_eps:.2f}"
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col4:
        avg_growth = df_filtered['年營收成長率'].mean() if not df_filtered.empty else 0
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric(
            label="📊 平均年成長率 (%)",
            value=f"{avg_growth:.2f}%"
        )
        st.markdown('</div>', unsafe_allow_html=True)

def create_charts(df_filtered):
    """創建圖表"""
    if df_filtered.empty:
        st.warning("沒有符合條件的股票，無法顯示圖表")
        return
    
    # 只顯示 ROE vs EPS 散點圖
    fig_scatter = px.scatter(
        df_filtered, 
        x='ROE', 
        y='EPS',
        hover_data=['stock_code', 'name'],
        title="ROE vs EPS 分布圖",
        labels={'ROE': 'ROE (%)', 'EPS': 'EPS'},
        color='年營收成長率',
        color_continuous_scale='viridis'
    )
    fig_scatter.update_layout(
        title_font_size=16,
        title_x=0.5,
        width=800,
        height=500
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

def main():
    # 主標題
    st.markdown('<h1 class="main-header">台灣股票篩選工具</h1>', unsafe_allow_html=True)
    
    # 載入數據
    df, file_info = load_stock_data()
    
    if df is None:
        st.error(f"⚠️ {file_info}")
        st.info("請確保有股票數據文件在 data/processed/ 目錄下")
        return
    
    # 從 file_info 中提取實際的文件路徑
    if " (" in file_info:
        actual_file_path = file_info.split(" (")[0]
    else:
        actual_file_path = file_info
    
    st.success(f"✅ 成功載入數據: {file_info}")
    
    # 安全地獲取文件更新時間
    try:
        if os.path.exists(actual_file_path):
            update_time = datetime.fromtimestamp(os.path.getctime(actual_file_path)).strftime('%Y-%m-%d %H:%M:%S')
            st.info(f"📅 最後更新時間: {update_time}")
        else:
            st.info("📅 文件時間信息不可用")
    except Exception:
        st.info("📅 文件時間信息不可用")
    
    # 側邊欄篩選條件
    st.sidebar.markdown('<div class="filter-header">篩選條件設定</div>', unsafe_allow_html=True)
    
    # ROE 篩選 - 改為滑動條，範圍 -100 到 100
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
    
    # EPS 篩選 - 改為滑動條
    st.sidebar.subheader("💰 EPS 最低標準")
    eps_default = st.session_state.get('eps_preset', 1.2)
    eps_min = st.sidebar.slider(
        "EPS 最低值",
        min_value=float(df['EPS'].min()),
        max_value=float(df['EPS'].max()),
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
    <div class="criteria-text">
    <strong>篩選條件：</strong> ROE > {roe_min:.1f}%, EPS > {eps_min:.1f}, 
    年營收成長率 > {annual_growth_min:.1f}%, 月營收成長率 > {monthly_growth_min:.1f}%
    </div>
    ''', unsafe_allow_html=True)
    
    # 執行篩選
    df_filtered = df[
        (df['ROE'] > roe_min) &
        (df['EPS'] > eps_min) &
        (df['年營收成長率'] > annual_growth_min) &
        (df['月營收成長率'] > monthly_growth_min)
    ].copy()
    
    # 顯示統計指標
    display_metrics(df_filtered, df)
    
    # 篩選結果
    st.markdown('<h2 class="result-header">符合條件的股票</h2>', unsafe_allow_html=True)
    
    if df_filtered.empty:
        st.warning("⚠️ 沒有股票符合您設定的篩選條件，請調整篩選參數")
        st.info("💡 建議放寬篩選條件，例如降低 ROE 或成長率要求")
    else:
        # 按ROE排序
        df_filtered = df_filtered.sort_values('ROE', ascending=False)
        
        # 格式化顯示
        df_display = df_filtered.copy()
        df_display['ROE'] = df_display['ROE'].round(2).astype(str) + '%'
        df_display['EPS'] = df_display['EPS'].round(2)
        df_display['年營收成長率'] = df_display['年營收成長率'].round(2).astype(str) + '%'
        df_display['月營收成長率'] = df_display['月營收成長率'].round(2).astype(str) + '%'
        
        # 重新命名欄位
        df_display = df_display.rename(columns={
            'stock_code': '股票代碼',
            'name': '股票名稱',
            'ROE': 'ROE(%)',
            'EPS': 'EPS',
            '年營收成長率': '年營收成長率(%)',
            '月營收成長率': '月營收成長率(%)'
        })
        
        st.dataframe(
            df_display,
            use_container_width=True,
            hide_index=True,
            column_config={
                "股票代碼": st.column_config.TextColumn("股票代碼", width="small"),
                "股票名稱": st.column_config.TextColumn("股票名稱", width="large"),
                "ROE(%)": st.column_config.TextColumn("ROE(%)", width="small"),
                "EPS": st.column_config.NumberColumn("EPS", width="small"),
                "年營收成長率(%)": st.column_config.TextColumn("年營收成長率(%)", width="medium"),
                "月營收成長率(%)": st.column_config.TextColumn("月營收成長率(%)", width="medium"),
            }
        )
        
        # 下載功能
        csv = df_filtered.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="📥 下載篩選結果 (CSV)",
            data=csv,
            file_name=f"filtered_stocks_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    
    # 圖表分析
    if show_charts and not df_filtered.empty:
        st.markdown("---")
        st.markdown("## 📊 數據分析圖表")
        create_charts(df_filtered)
    
    # 原始資料顯示
    if show_raw_data:
        st.markdown("---")
        st.markdown("## 📋 所有股票原始資料")
        
        # 搜尋功能
        search_term = st.text_input("🔍 搜尋股票 (代碼或名稱):", placeholder="例如: 2330 或 台積電")
        
        if search_term:
            mask = (df['stock_code'].str.contains(search_term, case=False, na=False) |
                   df['name'].str.contains(search_term, case=False, na=False))
            df_search = df[mask]
        else:
            df_search = df
        
        st.dataframe(
            df_search,
            use_container_width=True,
            hide_index=True
        )
    
    # 頁腳
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #7f8c8d; margin-top: 2rem;'>
        <p>📈 台灣股票篩選工具 | 數據僅供參考，投資請謹慎評估風險</p>
        <p>⏰ 最後更新: {}</p>
    </div>
    """.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')), unsafe_allow_html=True)

if __name__ == "__main__":
    main() 