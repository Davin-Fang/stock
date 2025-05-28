import streamlit as st
import pandas as pd
import glob
import os

st.set_page_config(
    page_title="股票營收成長率篩選工具",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 取得最新的 stock_data_*.csv
files = glob.glob('data/processed/stock_data_*.csv')
if not files:
    st.error("找不到任何股票資料檔案，請先執行資料蒐集！")
    st.stop()
latest_file = max(files, key=os.path.getctime)
df = pd.read_csv(latest_file)

# 檢查欄位
if '月營收成長率' not in df.columns:
    st.error("找不到「月營收成長率」欄位，請確認資料內容！")
    st.write("所有欄位：", df.columns.tolist())
    st.stop()

# 側邊欄 - 月營收成長率篩選
st.sidebar.title("篩選條件")
growth_min, growth_max = float(df['月營收成長率'].min()), float(df['月營收成長率'].max())
growth = st.sidebar.slider(
    "月營收成長率 (%)",
    min_value=round(growth_min, 2),
    max_value=round(growth_max, 2),
    value=(max(0.0, round(growth_min, 2)), round(growth_max, 2)),
    step=0.1
)

st.sidebar.markdown("""
- 只顯示「月營收成長率」欄位
- 篩選條件可調整
- 資料來源：`data/processed/` 目錄下最新檔案
""")

# 主畫面
st.title("📈 股票月營收成長率篩選工具")
st.markdown(f"**目前分析檔案：** `{os.path.basename(latest_file)}`")
st.markdown("""
本工具可協助你快速篩選出月營收成長率表現突出的股票。

- 只針對「月營收成長率」欄位進行篩選
- 可調整成長率區間
""")

# 篩選資料
df_filtered = df[(df['月營收成長率'] >= growth[0]) & (df['月營收成長率'] <= growth[1])]

st.subheader(f"篩選結果（共 {len(df_filtered)} 檔）")
st.dataframe(df_filtered.reset_index(drop=True), use_container_width=True)

with st.expander("顯示所有原始資料"):
    st.dataframe(df, use_container_width=True) 