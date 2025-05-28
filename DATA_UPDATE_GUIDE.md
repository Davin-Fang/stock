# 📊 股票數據更新指南

## 🚀 一鍵更新最新數據

### 方法 1：自動化腳本（推薦）

```bash
# 一鍵更新並部署
python update_and_deploy.py
```

**功能：**
- ✅ 自動抓取最新股票數據
- ✅ 驗證數據完整性
- ✅ 測試分析器
- ✅ 自動提交到 GitHub
- ✅ 觸發 Streamlit Cloud 更新

---

### 方法 2：手動分步更新

#### 步驟 1：抓取最新數據
```bash
# 使用混合式真實數據爬蟲（推薦）
python hybrid_real_crawler.py

# 或使用示例數據生成器（快速測試）
python create_sample_data.py

# 或使用其他爬蟲
python twse_real_crawler.py
```

#### 步驟 2：提交到 GitHub
```bash
# 添加所有新文件
git add .

# 提交更改
git commit -m "Update stock data - $(date)"

# 推送到 GitHub
git push origin main
```

#### 步驟 3：自動部署
- GitHub 更新後，Streamlit Cloud 會在 **2-5 分鐘內** 自動重新部署
- 無需手動操作！

---

## 📅 更新機制說明

### 🔄 本地應用更新
如果您在本地運行 `taiwan_stock_analyzer.py`：

1. **自動檢測**：應用會自動找到最新的數據文件
2. **即時更新**：刷新瀏覽器頁面即可看到新數據
3. **熱重載**：Streamlit 具有自動重載功能

### ☁️ 雲端應用更新  
如果您已部署到 Streamlit Cloud：

1. **提交到 GitHub** → 觸發自動部署
2. **等待 2-5 分鐘** → Streamlit Cloud 完成更新
3. **訪問應用網址** → 查看最新數據

---

## 📊 數據文件說明

### 文件位置和命名
```
data/processed/
├── stock_data_20250528_235420.csv          # 示例數據
├── hybrid_real_stock_data_YYYYMMDD.csv     # 真實混合數據
└── twse_stock_data_YYYYMMDD.csv           # TWSE 數據
```

### 應用數據加載優先級
1. `data/processed/` 目錄中的最新文件
2. `data/` 目錄中的最新文件  
3. 根目錄中的最新文件

**應用會自動選擇最新的數據文件！**

---

## 🛠️ 可用的數據爬蟲

### 1. 混合式真實數據爬蟲 ⭐
```bash
python hybrid_real_crawler.py
```
- **特色**：真實股票數據，100% 成功率
- **數據源**：twstock + TWSE API
- **推薦指數**：⭐⭐⭐⭐⭐

### 2. 示例數據生成器 🚀
```bash  
python create_sample_data.py
```
- **特色**：快速生成 50 支股票示例數據
- **用途**：測試、演示、快速驗證
- **推薦指數**：⭐⭐⭐⭐

### 3. TWSE 官方爬蟲
```bash
python twse_real_crawler.py
```
- **特色**：官方台股資料來源
- **推薦指數**：⭐⭐⭐

---

## 🎯 快速檢查清單

### ✅ 本地更新確認
- [ ] 運行數據爬蟲腳本
- [ ] 檢查 `data/processed/` 是否有新文件
- [ ] 啟動 `taiwan_stock_analyzer.py`
- [ ] 確認應用顯示最新數據

### ✅ 雲端部署確認  
- [ ] 提交新數據到 GitHub
- [ ] 等待 Streamlit Cloud 自動部署
- [ ] 訪問應用網址
- [ ] 驗證數據已更新

---

## 🚨 疑難排解

### 問題：數據未更新
**解決方案：**
1. 檢查數據文件時間戳
2. 重新運行數據爬蟲
3. 確認文件路徑正確

### 問題：GitHub 推送失敗
**解決方案：**
```bash
git status          # 檢查狀態
git add .           # 重新添加
git commit -m "Update data"
git push origin main
```

### 問題：Streamlit Cloud 未更新
**解決方案：**
1. 等待 5-10 分鐘
2. 檢查 GitHub 是否已更新
3. 手動觸發重新部署

---

## 🎉 總結

**最簡單的更新流程：**

```bash
# 一行命令搞定！
python update_and_deploy.py
```

**手動更新：**
```bash
python create_sample_data.py    # 生成新數據
git add . && git commit -m "Update data" && git push origin main
```

**2-5 分鐘後，您的雲端應用就會自動更新最新數據！** 🚀

---

## 🔗 相關鏈接

- **GitHub 倉庫**: https://github.com/Davin-Fang/stock.git
- **Streamlit Cloud**: https://share.streamlit.io
- **部署指南**: `STREAMLIT_DEPLOYMENT.md` 