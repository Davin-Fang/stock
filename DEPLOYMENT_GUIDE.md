# 🌐 台灣股票篩選工具 - 網路部署指南

讓您的股票分析工具上線，供全世界使用！

## 🚀 推薦部署方案

### 1. Streamlit Cloud (最推薦 - 完全免費)

**優點**: 
- ✅ 完全免費
- ✅ 專為 Streamlit 優化
- ✅ 自動 SSL 證書
- ✅ 簡單易用

**步驟**:
1. **將代碼推送到 GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin [YOUR_GITHUB_REPO_URL]
   git push -u origin main
   ```

2. **部署到 Streamlit Cloud**
   - 訪問: https://share.streamlit.io
   - 點擊 "New app"
   - 連接您的 GitHub 帳號
   - 選擇您的倉庫
   - 主文件路徑: `taiwan_stock_analyzer.py`
   - 點擊 "Deploy!"

3. **等待部署完成**
   - 通常需要 2-5 分鐘
   - 您會獲得一個類似 `https://your-app-name.streamlit.app` 的網址

---

### 2. Railway (免費層 + 簡單)

**優點**:
- ✅ 每月 $5 免費額度
- ✅ 支援多種語言
- ✅ 自動 HTTPS
- ✅ 簡單部署

**步驟**:
1. **準備代碼** (已完成)
2. **訪問 Railway**
   - 網址: https://railway.app
   - 使用 GitHub 登入
3. **創建新項目**
   - 點擊 "New Project"
   - 選擇 "Deploy from GitHub repo"
   - 選擇您的倉庫
4. **部署會自動開始**
   - Railway 會自動檢測 Python 應用
   - 使用我們的 `railway.json` 配置

---

### 3. Render (免費層)

**優點**:
- ✅ 免費層 (有限制)
- ✅ 自動 SSL
- ✅ 支援靜態網站和服務

**步驟**:
1. **創建 Render 帳號**
   - 網址: https://render.com
2. **創建新 Web Service**
   - 連接 GitHub 倉庫
   - 選擇您的倉庫
3. **配置設置**:
   ```
   Build Command: pip install -r requirements.txt
   Start Command: streamlit run taiwan_stock_analyzer.py --server.port=$PORT --server.address=0.0.0.0
   ```

---

### 4. Heroku (免費層已停止，付費選項)

**注意**: Heroku 已停止免費層服務，現在需要付費。

**步驟**:
1. **創建 Heroku 應用**
2. **添加 Procfile**:
   ```
   web: streamlit run taiwan_stock_analyzer.py --server.port=$PORT --server.address=0.0.0.0
   ```

---

## 📋 部署前檢查清單

- ✅ `requirements.txt` 包含所有依賴
- ✅ `taiwan_stock_analyzer.py` 是主應用文件
- ✅ 數據文件在 `data/processed/` 目錄
- ✅ `.streamlit/config.toml` 配置文件存在
- ✅ `README.md` 包含使用說明

## 🔧 常見問題解決

### 問題 1: 找不到數據文件
**解決方案**: 確保數據文件包含在 Git 倉庫中，或使用示例數據生成器：
```bash
python create_sample_data.py
```

### 問題 2: 依賴包安裝失敗
**解決方案**: 檢查 `requirements.txt` 中的版本兼容性

### 問題 3: 端口配置錯誤
**解決方案**: 確保使用環境變量 `$PORT`：
```python
port = int(os.environ.get("PORT", 8501))
```

## 🌟 部署後優化

### 性能優化
1. **數據緩存**: 使用 `@st.cache_data` 裝飾器
2. **圖片優化**: 壓縮靜態資源
3. **數據庫**: 考慮使用雲端數據庫

### 安全考慮
1. **環境變量**: 敏感信息使用環境變量
2. **HTTPS**: 確保啟用 SSL/TLS
3. **速率限制**: 防止濫用

## 📊 成本估算

| 平台 | 免費額度 | 付費起價 | 推薦度 |
|------|----------|----------|--------|
| Streamlit Cloud | 完全免費 | N/A | ⭐⭐⭐⭐⭐ |
| Railway | $5/月 | $5/月 | ⭐⭐⭐⭐ |
| Render | 750小時/月 | $7/月 | ⭐⭐⭐ |
| Heroku | 已停止 | $5/月 | ⭐⭐ |

## 🎯 推薦路徑

1. **新手**: 先用 Streamlit Cloud (免費 + 簡單)
2. **進階**: 需要更多控制時考慮 Railway 或 Render
3. **企業**: 考慮 AWS、Google Cloud 或 Azure

## 📞 技術支援

部署遇到問題？
- 📖 查看各平台官方文檔
- 🐛 檢查 GitHub Issues
- 💬 在社群論壇求助

---

**🎉 恭喜！您的台灣股票篩選工具即將上線服務全球投資者！** 