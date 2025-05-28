#!/usr/bin/env python3
"""
增強版台灣股票數據爬蟲
專門抓取 ROE、EPS、年營收成長率、月營收成長率等關鍵指標
與股票分析工具完全兼容
"""

import pandas as pd
import time
from datetime import datetime, timedelta
import os
import random
import requests
from collections import deque
import json
import yfinance as yf
import numpy as np
from bs4 import BeautifulSoup

class EnhancedStockCrawler:
    def __init__(self):
        self.batch_size = 5  # 每批處理5支股票
        self.sleep_time = 15  # 批次之間的等待時間（15秒）
        self.request_delay = 3  # 請求之間的延遲時間（3秒）
        self.max_retries = 3  # 最大重試次數
        self.retry_delay = 30  # 重試等待時間（30秒）
        
        # 設定資料夾路徑
        self.data_dir = 'data'
        self.raw_dir = os.path.join(self.data_dir, 'raw')
        self.processed_dir = os.path.join(self.data_dir, 'processed')
        self.logs_dir = os.path.join(self.data_dir, 'logs')
        
        # 確保資料夾存在
        for directory in [self.data_dir, self.raw_dir, self.processed_dir, self.logs_dir]:
            if not os.path.exists(directory):
                os.makedirs(directory)
        
        # 設定檔案路徑
        self.taiwan_stocks_file = os.path.join(self.raw_dir, 'taiwan_stocks.txt')
        self.failed_stocks_file = os.path.join(self.raw_dir, 'failed_stocks.txt')
        self.interim_file = os.path.join(self.raw_dir, f'interim_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')
        self.final_file = os.path.join(self.processed_dir, f'stock_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')
        self.log_file = os.path.join(self.logs_dir, f'enhanced_crawler_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
        
        # 設定請求標頭
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        # 台灣知名股票清單（較完整版本）
        self.taiwan_stocks = [
            # 台積電相關
            ('2330', '台積電'), ('3711', '日月光投控'), ('2454', '聯發科'),
            ('2303', '聯電'), ('3034', '聯詠'), ('3443', '創意'),
            ('6415', '矽力-KY'), ('3231', '緯創'), ('6669', '緯穎'),
            
            # 金融股
            ('2891', '中信金'), ('2882', '國泰金'), ('2881', '富邦金'),
            ('2886', '兆豐金'), ('2884', '玉山金'), ('2892', '第一金'),
            ('2885', '元大金'), ('2888', '新光金'), ('5880', '合庫金'),
            
            # 傳統產業
            ('2317', '鴻海'), ('2002', '中鋼'), ('1301', '台塑'),
            ('1303', '南亞'), ('6505', '台塑化'), ('1101', '台泥'),
            ('1102', '亞泥'), ('1216', '統一'), ('2105', '正新'),
            
            # 電子股
            ('2382', '廣達'), ('2357', '華碩'), ('2376', '技嘉'),
            ('2379', '瑞昱'), ('2385', '群光'), ('2327', '國巨'),
            ('2344', '華邦電'), ('2301', '光寶科'), ('2308', '台達電'),
            ('2360', '致茂'), ('2409', '友達'), ('2408', '南亞科'),
            
            # 通訊電信
            ('2412', '中華電'), ('3045', '台灣大'), ('4904', '遠傳'),
            ('2474', '可成'), ('3008', '大立光'), ('2395', '研華'),
            
            # 航運股
            ('2603', '長榮'), ('2609', '陽明'), ('2615', '萬海'),
            ('2204', '中華'), ('2207', '和泰車'),
            
            # 其他
            ('2323', '中環'), ('2912', '統一超'),
            
            # 擴展更多股票代碼（主要上市公司）
            ('1326', '台化'), ('1605', '華新'), ('2201', '裕隆'),
            ('2227', '裕日車'), ('2324', '仁寶'), ('2347', '聯強'),
            ('2353', '宏碁'), ('2356', '英業達'), ('2371', '大同'),
            ('2377', '微星'), ('2383', '台光電'), ('2392', '正崴'),
            ('2404', '漢唐'), ('2406', '國碩'), ('2419', '仲琦'),
            ('2441', '超豐'), ('2449', '京元電子'), ('2451', '創見'),
            ('2458', '義隆'), ('2477', '美隆電'), ('2492', '華新科'),
            ('2495', '普安'), ('2498', '宏達電'), ('2542', '興富發'),
            ('2548', '華固'), ('2597', '潤弘'), ('2633', '台灣高鐵'),
            ('2801', '彰銀'), ('2809', '京城銀'), ('2820', '華票'),
            ('2823', '中壽'), ('2832', '台產'), ('2834', '臺企銀'),
            ('2836', '高雄銀'), ('2838', '聯邦銀'), ('2845', '遠東銀'),
            ('2849', '安泰銀'), ('2850', '新產'), ('2851', '中再保'),
            ('2852', '第一保'), ('2855', '統一證'), ('2867', '三商壽'),
            ('2880', '華南金'), ('2883', '開發金'), ('2887', '台新金'),
            ('2889', '國票金'), ('2890', '永豐金'), ('2891', '中信金'),
            ('2912', '統一超'), ('3036', '文曄'), ('3042', '晶技'),
            ('3044', '健鼎'), ('3047', '訊舟'), ('3049', '和鑫'),
            ('3051', '力特'), ('3052', '夆典'), ('3054', '立德'),
            ('3056', '總太'), ('3057', '喬鼎'), ('3058', '立德'),
            ('3059', '華晶科'), ('3060', '銘異'), ('3092', '鴻碩'),
            ('4938', '和碩'), ('4958', '臻鼎-KY'), ('6176', '瑞儀'),
            ('6239', '力成'), ('6271', '同欣電'), ('6285', '啟碁'),
            ('8046', '南電'), ('8261', '富鼎'), ('8299', '群聯'),
            ('9910', '豐泰'), ('9917', '中保科'), ('9921', '巨大'),
            ('9930', '中聯資源'), ('9933', '中鼎'), ('9934', '成霖'),
            ('9935', '慶豐富'), ('9937', '全國'), ('9938', '百和'),
            ('9939', '宏全'), ('9940', '信義'), ('9941', '裕融'),
            ('9942', '茂順'), ('9943', '好樂迪'), ('9944', '新麗'),
            ('9945', '潤泰新'), ('9946', '三發地產'), ('9955', '佳龍'),
        ]
        
        # 初始化股票清單文件
        self.initialize_stock_list()
    
    def log_message(self, message):
        """記錄訊息到日誌檔案"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] {message}\n"
        
        # 同時輸出到控制台和日誌檔案
        print(message)
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)
    
    def initialize_stock_list(self):
        """初始化台灣股票清單"""
        if not os.path.exists(self.taiwan_stocks_file):
            with open(self.taiwan_stocks_file, 'w', encoding='utf-8') as f:
                for code, name in self.taiwan_stocks:
                    f.write(f"{code}.TW,{name}\n")
            self.log_message(f"已生成台灣股票清單: {len(self.taiwan_stocks)} 支股票")
        else:
            self.log_message(f"使用現有的台灣股票清單: {self.taiwan_stocks_file}")
    
    def get_stock_financials_yfinance(self, stock_code):
        """使用 yfinance 獲取股票財務數據"""
        try:
            stock = yf.Ticker(stock_code)
            info = stock.info
            
            # 檢查股票是否有效
            if not info or 'longName' not in info:
                return None
            
            # 獲取基本財務指標
            roe = info.get('returnOnEquity', 0)
            if roe and not np.isnan(roe):
                roe = roe * 100  # 轉換為百分比
            else:
                roe = 0
            
            eps = info.get('trailingEps', 0)
            if eps and np.isnan(eps):
                eps = 0
                
            # 獲取財務報表數據計算成長率
            try:
                # 獲取年度財務數據
                financials = stock.financials
                yearly_revenue_growth = 0
                
                if financials is not None and not financials.empty and len(financials.columns) >= 2:
                    # 尋找營收相關欄位
                    revenue_keys = ['Total Revenue', 'Revenue', 'Net Sales', 'Sales']
                    revenue_row = None
                    
                    for key in revenue_keys:
                        if key in financials.index:
                            revenue_row = financials.loc[key]
                            break
                    
                    if revenue_row is not None and len(revenue_row) >= 2:
                        current_revenue = revenue_row.iloc[0]
                        previous_revenue = revenue_row.iloc[1]
                        
                        if previous_revenue and previous_revenue != 0 and not np.isnan(previous_revenue):
                            yearly_revenue_growth = ((current_revenue - previous_revenue) / previous_revenue) * 100
                
                # 獲取季度數據計算月營收成長率
                quarterly_financials = stock.quarterly_financials
                monthly_revenue_growth = 0
                
                if quarterly_financials is not None and not quarterly_financials.empty and len(quarterly_financials.columns) >= 2:
                    revenue_keys = ['Total Revenue', 'Revenue', 'Net Sales', 'Sales']
                    revenue_row = None
                    
                    for key in revenue_keys:
                        if key in quarterly_financials.index:
                            revenue_row = quarterly_financials.loc[key]
                            break
                    
                    if revenue_row is not None and len(revenue_row) >= 4:
                        # 計算最近季度與去年同期的比較
                        current_quarter = revenue_row.iloc[0]
                        year_ago_quarter = revenue_row.iloc[3] if len(revenue_row) > 3 else revenue_row.iloc[-1]
                        
                        if year_ago_quarter and year_ago_quarter != 0 and not np.isnan(year_ago_quarter):
                            monthly_revenue_growth = ((current_quarter - year_ago_quarter) / year_ago_quarter) * 100
                
            except Exception as e:
                self.log_message(f"計算 {stock_code} 成長率時發生錯誤: {str(e)}")
                yearly_revenue_growth = 0
                monthly_revenue_growth = 0
            
            return {
                'stock_code': stock_code,
                'name': info.get('longName', info.get('shortName', '')),
                'ROE': round(roe, 2),
                'EPS': round(eps, 2),
                '年營收成長率': round(yearly_revenue_growth, 2),
                '月營收成長率': round(monthly_revenue_growth, 2),
                'market_cap': info.get('marketCap', 0),
                'sector': info.get('sector', ''),
                'industry': info.get('industry', '')
            }
            
        except Exception as e:
            self.log_message(f"yfinance 獲取 {stock_code} 數據時發生錯誤: {str(e)}")
            return None
    
    def get_taiwan_stock_data(self, stock_code, stock_name):
        """獲取台灣股票數據的主函數"""
        self.log_message(f"正在處理 {stock_code} ({stock_name})...")
        
        # 首先嘗試使用 yfinance
        data = self.get_stock_financials_yfinance(stock_code)
        
        if data:
            # 使用提供的中文名稱（如果 yfinance 沒有提供好的名稱）
            if not data['name'] or len(data['name']) < 2:
                data['name'] = stock_name
            
            self.log_message(f"✅ 成功獲取 {stock_code} 數據")
            return data
        else:
            # 如果 yfinance 失敗，創建基本記錄
            self.log_message(f"⚠️ {stock_code} 數據獲取失敗，使用預設值")
            return {
                'stock_code': stock_code,
                'name': stock_name,
                'ROE': 0,
                'EPS': 0,
                '年營收成長率': 0,
                '月營收成長率': 0,
                'market_cap': 0,
                'sector': '',
                'industry': ''
            }
    
    def process_batch(self, batch):
        """處理一批股票"""
        results = []
        successful_count = 0
        
        for stock_code, stock_name in batch:
            try:
                data = self.get_taiwan_stock_data(stock_code, stock_name)
                if data:
                    results.append(data)
                    if data['ROE'] > 0 or data['EPS'] > 0:  # 有效數據
                        successful_count += 1
                
                # 請求之間的延遲
                time.sleep(self.request_delay + random.uniform(0.5, 1.5))
                
            except Exception as e:
                self.log_message(f"❌ 處理 {stock_code} 時發生錯誤: {str(e)}")
                continue
        
        if results:
            self.save_results(results)
            self.log_message(f"✅ 批次完成: {successful_count}/{len(batch)} 支股票成功獲取有效數據")
        
        return results
    
    def save_results(self, results):
        """保存結果到CSV文件"""
        if not results:
            return
        
        df = pd.DataFrame(results)
        
        # 確保欄位順序與分析工具一致
        column_order = ['stock_code', 'name', 'ROE', 'EPS', '年營收成長率', '月營收成長率', 
                       'market_cap', 'sector', 'industry']
        df = df.reindex(columns=column_order, fill_value=0)
        
        # 如果文件存在，則追加；否則創建新文件
        if os.path.exists(self.interim_file):
            df.to_csv(self.interim_file, mode='a', header=False, index=False, encoding='utf-8-sig')
        else:
            df.to_csv(self.interim_file, index=False, encoding='utf-8-sig')
        
        self.log_message(f"💾 已保存 {len(results)} 筆數據到 {os.path.basename(self.interim_file)}")
    
    def crawl_all_stocks(self):
        """爬取所有台灣股票數據"""
        self.log_message("🚀 開始爬取台灣股票數據...")
        self.log_message("📊 目標指標: ROE、EPS、年營收成長率、月營收成長率")
        self.log_message("⏰ 這個過程可能需要較長時間，程式會定期保存中間結果")
        self.log_message("🛑 您可以隨時按 Ctrl+C 中斷程式，已處理的數據會被保存")
        
        try:
            # 讀取台灣股票清單
            stocks_to_process = []
            with open(self.taiwan_stocks_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if ',' in line:
                        parts = line.strip().split(',')
                        stock_code = parts[0]
                        stock_name = parts[1] if len(parts) > 1 else ''
                        stocks_to_process.append((stock_code, stock_name))
            
            self.log_message(f"📋 找到 {len(stocks_to_process)} 支台灣股票")
            
            # 批次處理
            total_batches = (len(stocks_to_process) + self.batch_size - 1) // self.batch_size
            all_results = []
            
            for i in range(0, len(stocks_to_process), self.batch_size):
                batch = stocks_to_process[i:i + self.batch_size]
                batch_num = i // self.batch_size + 1
                
                self.log_message(f"\n📦 處理第 {batch_num}/{total_batches} 批")
                self.log_message(f"🎯 股票: {[f'{code}({name})' for code, name in batch]}")
                
                batch_results = self.process_batch(batch)
                all_results.extend(batch_results)
                
                # 批次之間的等待
                if i + self.batch_size < len(stocks_to_process):
                    self.log_message(f"⏳ 等待 {self.sleep_time} 秒後處理下一批...")
                    time.sleep(self.sleep_time)
            
            # 處理完成後，整理並保存最終結果
            if os.path.exists(self.interim_file):
                # 讀取所有中間結果
                df = pd.read_csv(self.interim_file)
                
                # 數據清理和驗證
                self.log_message("🔧 進行數據清理和驗證...")
                
                # 移除重複項
                df = df.drop_duplicates(subset=['stock_code'], keep='last')
                
                # 確保數值欄位為數字類型
                for col in ['ROE', 'EPS', '年營收成長率', '月營收成長率']:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                
                # 保存最終結果
                df.to_csv(self.final_file, index=False, encoding='utf-8-sig')
                
                # 生成統計報告
                self.generate_report(df)
                
                self.log_message(f"🎉 所有數據已保存到 {os.path.basename(self.final_file)}")
                
        except KeyboardInterrupt:
            self.log_message("\n⏹️ 程式被使用者中斷")
            if os.path.exists(self.interim_file):
                self.log_message(f"💾 已處理的數據已保存到 {os.path.basename(self.interim_file)}")
        except Exception as e:
            self.log_message(f"❌ 爬取股票數據時發生錯誤: {str(e)}")
    
    def generate_report(self, df):
        """生成數據統計報告"""
        self.log_message("\n📊 數據統計報告:")
        self.log_message(f"總股票數: {len(df)}")
        
        # 有效數據統計
        valid_roe = df[df['ROE'] > 0]
        valid_eps = df[df['EPS'] > 0]
        valid_annual_growth = df[df['年營收成長率'] != 0]
        valid_monthly_growth = df[df['月營收成長率'] != 0]
        
        self.log_message(f"有效 ROE 數據: {len(valid_roe)} 支 ({len(valid_roe)/len(df)*100:.1f}%)")
        self.log_message(f"有效 EPS 數據: {len(valid_eps)} 支 ({len(valid_eps)/len(df)*100:.1f}%)")
        self.log_message(f"有效年營收成長率: {len(valid_annual_growth)} 支 ({len(valid_annual_growth)/len(df)*100:.1f}%)")
        self.log_message(f"有效月營收成長率: {len(valid_monthly_growth)} 支 ({len(valid_monthly_growth)/len(df)*100:.1f}%)")
        
        # 數據範圍
        if len(valid_roe) > 0:
            self.log_message(f"ROE 範圍: {valid_roe['ROE'].min():.2f}% ~ {valid_roe['ROE'].max():.2f}%")
        if len(valid_eps) > 0:
            self.log_message(f"EPS 範圍: {valid_eps['EPS'].min():.2f} ~ {valid_eps['EPS'].max():.2f}")
        
        # 優質股票統計
        quality_stocks = df[
            (df['ROE'] > 15) & 
            (df['EPS'] > 0) & 
            (df['年營收成長率'] > 20) & 
            (df['月營收成長率'] > 20)
        ]
        
        self.log_message(f"🏆 優質股票 (ROE>15%, EPS>0, 年成長>20%, 月成長>20%): {len(quality_stocks)} 支")
        
        if len(quality_stocks) > 0:
            self.log_message("前5名優質股票:")
            top5 = quality_stocks.nlargest(5, 'ROE')
            for idx, row in top5.iterrows():
                self.log_message(f"  {row['stock_code']} {row['name']}: ROE={row['ROE']:.2f}%, EPS={row['EPS']:.2f}")
    
    def test_single_stock(self, stock_code, stock_name=None):
        """測試單一股票數據獲取"""
        self.log_message(f"🧪 測試獲取 {stock_code} 的數據...")
        
        if stock_name is None:
            # 從股票清單中尋找名稱
            try:
                with open(self.taiwan_stocks_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if stock_code in line:
                            parts = line.strip().split(',')
                            if len(parts) > 1:
                                stock_name = parts[1]
                                break
            except:
                pass
            
            if stock_name is None:
                stock_name = "測試股票"
        
        data = self.get_taiwan_stock_data(stock_code, stock_name)
        
        if data:
            self.log_message("✅ 測試成功！獲取的數據:")
            for key, value in data.items():
                self.log_message(f"  {key}: {value}")
            return True
        else:
            self.log_message("❌ 測試失敗！")
            return False

def main():
    """主函數"""
    print("🎯 增強版台灣股票數據爬蟲")
    print("=" * 50)
    
    crawler = EnhancedStockCrawler()
    
    # 詢問使用者要執行的操作
    print("\n請選擇要執行的操作:")
    print("1. 測試單一股票數據獲取")
    print("2. 爬取所有台灣股票數據")
    print("3. 查看現有數據統計")
    
    try:
        choice = input("\n請輸入選項 (1-3): ").strip()
        
        if choice == '1':
            # 測試單一股票
            test_code = input("請輸入要測試的股票代碼 (例如: 2330.TW): ").strip()
            crawler.test_single_stock(test_code)
            
        elif choice == '2':
            # 爬取所有數據
            confirm = input("確定要開始爬取所有股票數據嗎？這可能需要較長時間 (y/N): ").strip().lower()
            if confirm in ['y', 'yes']:
                crawler.crawl_all_stocks()
            else:
                print("操作已取消")
                
        elif choice == '3':
            # 查看現有數據
            import glob
            files = glob.glob(os.path.join(crawler.processed_dir, 'stock_data_*.csv'))
            if files:
                latest_file = max(files, key=os.path.getctime)
                df = pd.read_csv(latest_file)
                crawler.generate_report(df)
            else:
                print("找不到現有的數據文件")
        else:
            print("無效的選項")
            
    except KeyboardInterrupt:
        print("\n程式被中斷")
    except Exception as e:
        print(f"執行時發生錯誤: {str(e)}")

if __name__ == "__main__":
    main() 