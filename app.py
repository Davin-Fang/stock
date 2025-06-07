#!/usr/bin/env python3
"""
台灣股票分析平台 - Streamlit Cloud 部署入口
主要應用程序入口點
"""

# 導入主應用
from taiwan_stock_analyzer import main

if __name__ == "__main__":
    # 設定頁面基本配置（如果還沒設定的話）
    try:
        import streamlit as st
        # 如果還沒設定頁面配置，這裡會設定
        if not hasattr(st, '_config'):
            st.set_page_config(
                page_title="台灣股票分析平台",
                page_icon="📈",
                layout="wide",
                initial_sidebar_state="expanded",
            )
    except:
        pass
    
    # 執行主應用
    main() 