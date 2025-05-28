# 🎯 台灣股票篩選分析工具

一個功能強大的台灣股票篩選和分析工具，使用 Streamlit 構建，提供直觀的滑動條界面和多種投資策略預設。

## ✨ 主要功能

- 📊 **智能篩選**: 基於 ROE、EPS、年營收成長率、月營收成長率等關鍵指標
- 🎛️ **滑動條界面**: 直觀的橫拉調整，快速設定篩選條件
- ⚡ **快速預設**: 積極成長、價值投資、保守投資、高成長等策略一鍵設定
- 📈 **數據視覺化**: 互動式圖表分析，包含散點圖和分布圖
- 💾 **數據下載**: 篩選結果可導出為 CSV 格式
- 🔍 **搜尋功能**: 支援股票代碼或名稱快速搜尋

## 🚀 在線體驗

### 部署選項

1. **Streamlit Cloud** (推薦 - 免費)
2. **Heroku** (免費層)
3. **Railway** (免費層)
4. **Render** (免費層)

## 💻 本地安裝

### 前置需求
- Python 3.8+
- pip

### 安裝步驟

```bash
# 克隆專案
git clone [repository-url]
cd stock-analyzer

# 安裝依賴
pip install -r requirements.txt

# 運行應用
streamlit run taiwan_stock_analyzer.py
```

### 快速啟動
```bash
python start_analyzer.py
```

## 📊 使用說明

### 基本操作
1. **調整篩選條件**: 使用左側滑動條快速調整各項指標
2. **快速預設**: 點擊預設按鈕快速應用投資策略
3. **查看結果**: 符合條件的股票會即時顯示在主頁面
4. **下載數據**: 點擊下載按鈕獲取 CSV 格式結果

### 投資策略預設
- **💎 積極成長**: ROE>20%, EPS>2, 年成長>30%, 月成長>30%
- **💰 價值投資**: ROE>15%, EPS>1, 年成長>10%, 月成長>5%
- **🛡️ 保守投資**: ROE>10%, EPS>0.5, 年成長>5%, 月成長>0%
- **🔥 高成長**: ROE>5%, EPS>0, 年成長>50%, 月成長>40%

## 📁 項目結構

```
stock-analyzer/
├── taiwan_stock_analyzer.py    # 主應用程序
├── start_analyzer.py           # 啟動器
├── create_sample_data.py       # 示例數據生成器
├── requirements.txt           # 依賴包列表
├── data/                     # 數據目錄
│   └── processed/           # 處理後的股票數據
└── README.md                # 項目說明
```

## 🔧 技術棧

- **Frontend**: Streamlit
- **數據處理**: Pandas
- **視覺化**: Plotly
- **語言**: Python 3.8+

## 🌐 部署指南

### Streamlit Cloud 部署 (推薦)

1. 將代碼推送到 GitHub
2. 訪問 [share.streamlit.io](https://share.streamlit.io)
3. 連接 GitHub 倉庫
4. 選擇主文件: `taiwan_stock_analyzer.py`
5. 點擊部署

### 其他平台部署

詳細的部署指南請參考各平台官方文檔。

## ⚠️ 免責聲明

本工具僅供教育和研究用途，不構成投資建議。投資有風險，請謹慎評估後再做決定。

## 📞 支持

如有問題或建議，請提交 Issue 或 Pull Request。

---

**Made with ❤️ for Taiwan Stock Market Analysis** 