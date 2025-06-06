# 🚀 台灣股票分析平台 - Streamlit Cloud 部署指南

## 📋 部署前檢查清單

### ✅ 必要文件確認
- [x] `taiwan_stock_analyzer.py` - 主應用程序（已修復布局問題）
- [x] `app.py` - 應用入口點
- [x] `requirements.txt` - 依賴包列表（已更新版本）
- [x] `.streamlit/config.toml` - Streamlit 配置
- [x] `demo_data_generator.py` - 演示數據生成器

### ✅ 版本更新內容 (v3.3.0)
- **修復股票篩選條件位置**: 筛选条件已移回侧边栏
- **改善數據加載機制**: 支援雲端和本地雙模式
- **優化錯誤處理**: 更好的異常處理和回退機制
- **更新版本號**: 從 v3.2.1 更新到 v3.3.0

## 🛠️ 部署步驟

### 1. 確保 GitHub 倉庫最新
```bash
git add .
git commit -m "Fix: 修復篩選條件位置，優化雲端部署，更新到v3.3.0"
git push origin main
```

### 2. Streamlit Cloud 設定
- **Repository**: 你的 GitHub 倉庫
- **Branch**: `main`
- **Main file path**: `taiwan_stock_analyzer.py` 或 `app.py`

### 3. 環境變數設定（可選）
```
STREAMLIT_THEME_PRIMARY_COLOR = "#1f77b4"
STREAMLIT_THEME_BACKGROUND_COLOR = "#ffffff"
```

## 🔧 已修復的問題

### 問題 1: 篩選條件顯示位置錯誤 ✅ 已修復
**原因**: 篩選條件設定顯示在主頁面而非側邊欄  
**解決方案**: 
- 將所有篩選條件移到 `st.sidebar`
- 調整快速預設策略按鈕位置
- 優化側邊欄布局

### 問題 2: 版本號未更新 ✅ 已修復
**原因**: 版本號仍顯示 v3.2.1  
**解決方案**: 
- 更新到 v3.3.0
- 添加最新更新說明
- 記錄修復內容

### 問題 3: 數據載入錯誤 ✅ 已修復
**原因**: 雲端環境無法載入本地數據文件  
**解決方案**: 
- 添加示例數據回退機制
- 改善錯誤處理
- 提供數據獲取指引

### 問題 4: 依賴包版本問題 ✅ 已修復
**原因**: requirements.txt 缺少版本號  
**解決方案**: 
- 指定最低版本需求
- 確保包相容性
- 移除不必要依賴

## 📊 雲端vs本地功能對比

| 功能 | 雲端演示版 | 本地完整版 |
|------|-----------|-----------|
| 股票篩選 | ✅ 20支示例股票 | ✅ 765支完整股票 |
| 個股回測 | ✅ 5支主要股票 | ✅ 632支股票 |
| 批量回測結果 | ❌ 需本地數據 | ✅ 完整回測結果 |
| 投資組合分析 | ✅ 基本功能 | ✅ 完整功能 |

## 💡 使用說明

### 雲端演示版特點
1. **示例數據**: 包含20支台灣知名股票
2. **完整功能**: 所有核心功能都可正常使用
3. **教學目的**: 適合學習和演示使用

### 本地完整版優勢
1. **完整數據**: 765支股票 + 632支價格數據
2. **實時更新**: 可下載最新股票數據
3. **批量回測**: 已完成443支股票回測分析

## 🎯 部署後驗證

### 功能測試清單
- [ ] 應用正常啟動
- [ ] 側邊欄篩選條件正確顯示
- [ ] 股票篩選功能正常
- [ ] 個股回測功能正常
- [ ] 投資組合分析功能正常
- [ ] 版本號顯示為 v3.3.0

### 預期效果
1. **篩選條件**: 位於左側邊欄，包含滑桿和按鈕
2. **快速策略**: 三個按鈕在側邊欄下方
3. **數據載入**: 自動使用示例數據，顯示獲取指引
4. **版本資訊**: 顯示 v3.3.0 和最新更新內容

## 🐛 常見問題排除

### Q1: 篩選條件還是在右邊？
**A**: 清除瀏覽器快取，重新整理頁面

### Q2: 顯示數據載入錯誤？
**A**: 正常現象，雲端版本會自動使用示例數據

### Q3: 個股回測無法選股票？
**A**: 選擇「手動輸入股票代碼」，輸入 2330、2454、2317、1301、2382

### Q4: 版本號沒更新？
**A**: 確認 GitHub 已推送最新代碼，重新部署應用

## 📞 技術支援

### 本地部署指引
```bash
# 1. 克隆倉庫
git clone [your-repo-url]
cd stock-crowd

# 2. 安裝依賴
pip install -r requirements.txt

# 3. 生成演示數據（可選）
python demo_data_generator.py

# 4. 啟動應用
streamlit run taiwan_stock_analyzer.py
```

### 獲取完整數據
```bash
# 下載股票基礎數據
python hybrid_real_crawler.py

# 下載股價歷史數據  
python twse_data_downloader.py

# 執行批量回測
python batch_backtest.py
```

---

## 🎉 部署完成！

如果按照以上步驟執行，你的台灣股票分析平台應該可以在 Streamlit Cloud 上正常運行，所有功能都已修復和優化。

**線上演示版本**: 使用示例數據，展示完整功能  
**本地完整版本**: 支援完整的765支股票和回測分析

有任何問題請參考常見問題排除或聯繫技術支援。 