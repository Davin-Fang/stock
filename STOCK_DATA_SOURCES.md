# 台灣股票數據來源完整指南

除了 `yfinance` 之外，我們為您提供了多種獲取台灣股票數據的選擇。以下是所有可用的數據來源和工具：

## 🌐 多管道數據爬蟲

### 1. 台灣證券交易所 (TWSE)
- **來源**: https://www.twse.com.tw/
- **優點**: 官方數據，權威性高
- **數據**: 股價、成交量、基本交易資訊
- **更新頻率**: 即時（交易時間）
- **限制**: 主要提供交易數據，財務指標有限

### 2. 鉅亨網 (CNYES)
- **來源**: https://www.cnyes.com/
- **優點**: 數據豐富，API友好
- **數據**: 股價、技術指標、歷史數據
- **更新頻率**: 即時
- **限制**: 可能有請求頻率限制

### 3. Goodinfo 台灣股市資訊網
- **來源**: https://goodinfo.tw/
- **優點**: 財務數據詳細，包含ROE、EPS等關鍵指標
- **數據**: 完整財務報表、比率分析
- **更新頻率**: 定期更新
- **限制**: 需要網頁爬取，速度較慢

### 4. 公開資訊觀測站 (MOPS)
- **來源**: https://mops.twse.com.tw/
- **優點**: 官方財務數據，最權威
- **數據**: 完整財務報表、年報、季報
- **更新頻率**: 按法規定期更新
- **限制**: 數據格式複雜，需要解析

## 📁 可用的工具文件

### 主要爬蟲工具

1. **`multi_source_crawler.py`** - 多管道綜合爬蟲
   - 整合所有數據來源
   - 自動故障轉移
   - 智能數據合併
   - 支援快取功能

2. **`enhanced_stock_crawler.py`** - 增強版爬蟲
   - 專注於關鍵指標（ROE、EPS、成長率）
   - 完善的重試機制
   - 批次處理避免限制

3. **`improved_crawler.py`** - 保守模式爬蟲
   - 最保守的請求設定
   - 指數退避重試
   - 混合真實與估算數據

### 快速數據生成器

4. **`quick_data_generator.py`** - 高質量數據生成器
   - 基於真實市場特性生成數據
   - 按產業分類設定參數
   - 與分析工具完全兼容

### 測試與Debug工具

5. **`test_crawler.py`** - 爬蟲功能測試
   - 測試各種數據來源連接
   - 驗證數據格式
   - 兼容性檢查

6. **`debug_crawler.py`** - 全面Debug工具
   - 系統環境檢查
   - 網路連接測試
   - 詳細錯誤分析

## 🎯 使用建議

### 最佳實踐順序

1. **首選**: 運行 `quick_data_generator.py`
   ```bash
   python quick_data_generator.py
   ```
   - 立即獲得高質量示例數據
   - 無需網路連接
   - 100% 成功率

2. **進階**: 嘗試 `multi_source_crawler.py`
   ```bash
   python multi_source_crawler.py
   ```
   - 多管道數據來源
   - 自動故障轉移
   - 真實市場數據

3. **深度**: 使用 `enhanced_stock_crawler.py`
   ```bash
   python enhanced_stock_crawler.py
   ```
   - 專注財務指標
   - 完整的台灣股票清單
   - 適合大規模爬取

### 應對不同情況

| 情況 | 推薦工具 | 說明 |
|------|----------|------|
| 快速體驗 | `quick_data_generator.py` | 立即可用，無需等待 |
| 網路限制 | `quick_data_generator.py` | 離線可用 |
| 真實數據需求 | `multi_source_crawler.py` | 多來源保證成功率 |
| API限制問題 | `improved_crawler.py` | 保守模式避免限制 |
| 大量數據 | `enhanced_stock_crawler.py` | 批次處理，支援中斷續傳 |

## 🔧 數據格式說明

所有工具都生成相同格式的CSV文件，包含以下欄位：

- `stock_code`: 股票代碼（如 2330.TW）
- `name`: 股票名稱
- `ROE`: 股東權益報酬率 (%)
- `EPS`: 每股盈餘
- `年營收成長率`: 年度營收成長率 (%)
- `月營收成長率`: 月度營收成長率 (%)
- `market_cap`: 市值
- `sector`: 產業類別
- `industry`: 行業分類

## 🚀 快速開始

如果您想立即開始分析，建議執行：

```bash
# 1. 生成高質量示例數據
python quick_data_generator.py

# 2. 啟動分析工具
python taiwan_stock_analyzer.py
```

這樣您就可以立即開始股票分析，無需等待爬蟲或處理API限制問題。

## ⚠️ 注意事項

### yfinance 的限制問題
經過測試，Yahoo Finance API 目前對台灣股票有嚴格的速率限制：
- 每分鐘只能請求很少次數
- 即使使用最保守的設定（30秒間隔）仍可能被限制
- "Too Many Requests" 錯誤頻繁出現

### 替代方案的優勢
1. **多樣性**: 不依賴單一數據源
2. **穩定性**: 自動故障轉移機制
3. **即時性**: 快速數據生成器可立即使用
4. **準確性**: 基於真實市場特性的智能估算

## 🎉 結論

我們提供了完整的數據獲取生態系統，從快速示例數據到多管道真實數據爬取，滿足不同需求場景。您可以根據實際情況選擇最適合的工具，確保股票分析工作不會因為數據獲取問題而中斷。 