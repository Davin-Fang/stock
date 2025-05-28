#!/usr/bin/env python3
"""
改進版台灣股票爬蟲
包含完善的速率限制處理、重試機制、離線模式
專門抓取 ROE、EPS、年營收成長率、月營收成長率等關鍵指標
"""

import pandas as pd
import time
from datetime import datetime, timedelta
import os
import random
import requests
import yfinance as yf
import numpy as np
from functools import wraps

class ImprovedStockCrawler:
    def __init__(self):
        # 更保守的請求設定
        self.batch_size = 3  # 每批只處理3支股票
        self.sleep_time = 30  # 批次之間等待30秒
        self.request_delay = 10  # 請求之間等待10秒
        self.max_retries = 3
        self.retry_base_delay = 60  # 基礎重試延遲60秒
        
        # 資料夾設定
        self.data_dir = 'data'
        self.raw_dir = os.path.join(self.data_dir, 'raw')
        self.processed_dir = os.path.join(self.data_dir, 'processed')
        self.logs_dir = os.path.join(self.data_dir, 'logs')
        
        for directory in [self.data_dir, self.raw_dir, self.processed_dir, self.logs_dir]:
            os.makedirs(directory, exist_ok=True)
        
        # 檔案路徑
        self.taiwan_stocks_file = os.path.join(self.raw_dir, 'taiwan_stocks_list.txt')
        self.cache_file = os.path.join(self.raw_dir, 'stock_cache.csv')
        self.interim_file = os.path.join(self.raw_dir, f'interim_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')
        self.final_file = os.path.join(self.processed_dir, f'stock_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')
        self.log_file = os.path.join(self.logs_dir, f'improved_crawler_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
        
        # 台灣主要股票清單（精選版本）
        self.taiwan_stocks = [
            # 科技股 - 最重要的幾支
            ('2330', '台積電'), ('2454', '聯發科'), ('2317', '鴻海'),
            ('3711', '日月光投控'), ('2303', '聯電'),
            
            # 金融股
            ('2891', '中信金'), ('2882', '國泰金'), ('2881', '富邦金'),
            ('2886', '兆豐金'), ('2884', '玉山金'),
            
            # 傳統產業
            ('2002', '中鋼'), ('1301', '台塑'), ('1303', '南亞'),
            ('2105', '正新'), ('1216', '統一'),
            
            # 電子股
            ('2382', '廣達'), ('2357', '華碩'), ('2308', '台達電'),
            ('2327', '國巨'), ('2379', '瑞昱'),
            
            # 其他重要股票
            ('2412', '中華電'), ('2912', '統一超'), ('2207', '和泰車'),
            ('3008', '大立光'), ('2395', '研華')
        ]
        
        # 初始化
        self.initialize_stock_list()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def log_message(self, message):
        """記錄日誌"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] {message}"
        print(log_entry)
        
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry + '\n')
        except:
            pass
    
    def initialize_stock_list(self):
        """初始化股票清單"""
        if not os.path.exists(self.taiwan_stocks_file):
            with open(self.taiwan_stocks_file, 'w', encoding='utf-8') as f:
                for code, name in self.taiwan_stocks:
                    f.write(f"{code}.TW,{name}\n")
            self.log_message(f"已生成台灣股票清單: {len(self.taiwan_stocks)} 支股票")
        else:
            self.log_message(f"使用現有的台灣股票清單")
    
    def rate_limit_handler(func):
        """速率限制處理裝飾器"""
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            for attempt in range(self.max_retries):
                try:
                    result = func(self, *args, **kwargs)
                    return result
                except Exception as e:
                    error_str = str(e).lower()
                    if 'rate limit' in error_str or 'too many requests' in error_str:
                        wait_time = self.retry_base_delay * (2 ** attempt)  # 指數退避
                        self.log_message(f"遇到速率限制，等待 {wait_time} 秒... (嘗試 {attempt + 1}/{self.max_retries})")
                        time.sleep(wait_time)
                        if attempt == self.max_retries - 1:
                            self.log_message("已達最大重試次數，跳過此請求")
                            return None
                    else:
                        self.log_message(f"其他錯誤: {str(e)}")
                        return None
            return None
        return wrapper
    
    @rate_limit_handler
    def get_stock_data_safe(self, stock_code):
        """安全地獲取股票數據"""
        stock = yf.Ticker(stock_code)
        info = stock.info
        
        if not info or len(info) < 5:  # 基本檢查
            return None
        
        # 獲取基本指標
        roe = info.get('returnOnEquity', 0)
        if roe and not np.isnan(roe):
            roe = roe * 100
        else:
            roe = 0
        
        eps = info.get('trailingEps', 0)
        if eps and np.isnan(eps):
            eps = 0
        
        # 簡化版營收成長率計算
        annual_growth = 0
        quarterly_growth = 0
        
        try:
            # 嘗試獲取年度數據
            financials = stock.financials
            if financials is not None and not financials.empty and len(financials.columns) >= 2:
                revenue_keys = ['Total Revenue', 'Revenue']
                for key in revenue_keys:
                    if key in financials.index:
                        revenue_data = financials.loc[key]
                        if len(revenue_data) >= 2:
                            current = revenue_data.iloc[0]
                            previous = revenue_data.iloc[1]
                            if previous and previous != 0:
                                annual_growth = ((current - previous) / previous) * 100
                        break
        except:
            pass
        
        try:
            # 嘗試獲取季度數據
            quarterly = stock.quarterly_financials
            if quarterly is not None and not quarterly.empty and len(quarterly.columns) >= 4:
                revenue_keys = ['Total Revenue', 'Revenue']
                for key in revenue_keys:
                    if key in quarterly.index:
                        revenue_data = quarterly.loc[key]
                        if len(revenue_data) >= 4:
                            current_q = revenue_data.iloc[0]
                            year_ago_q = revenue_data.iloc[3]
                            if year_ago_q and year_ago_q != 0:
                                quarterly_growth = ((current_q - year_ago_q) / year_ago_q) * 100
                        break
        except:
            pass
        
        return {
            'stock_code': stock_code,
            'name': info.get('longName', info.get('shortName', '')),
            'ROE': round(roe, 2),
            'EPS': round(eps, 2),
            '年營收成長率': round(annual_growth, 2),
            '月營收成長率': round(quarterly_growth, 2),
            'market_cap': info.get('marketCap', 0),
            'sector': info.get('sector', ''),
            'industry': info.get('industry', '')
        }
    
    def load_cached_data(self):
        """載入快取數據"""
        if os.path.exists(self.cache_file):
            try:
                df = pd.read_csv(self.cache_file)
                self.log_message(f"載入快取數據: {len(df)} 支股票")
                return df
            except:
                pass
        return pd.DataFrame()
    
    def save_to_cache(self, data):
        """保存到快取"""
        try:
            df = pd.DataFrame(data)
            df.to_csv(self.cache_file, index=False, encoding='utf-8-sig')
            self.log_message(f"已保存到快取: {len(data)} 筆數據")
        except Exception as e:
            self.log_message(f"快取保存失敗: {str(e)}")
    
    def crawl_stocks_conservative(self):
        """保守模式爬取股票數據"""
        self.log_message("🚀 開始保守模式爬取台灣股票數據...")
        self.log_message("⚠️ 使用保守設定以避免速率限制")
        
        # 載入快取數據
        cached_df = self.load_cached_data()
        cached_codes = set(cached_df['stock_code'].tolist()) if not cached_df.empty else set()
        
        # 讀取股票清單
        stocks_to_process = []
        with open(self.taiwan_stocks_file, 'r', encoding='utf-8') as f:
            for line in f:
                if ',' in line:
                    parts = line.strip().split(',')
                    stock_code = parts[0]
                    stock_name = parts[1] if len(parts) > 1 else ''
                    
                    # 跳過已快取的股票
                    if stock_code not in cached_codes:
                        stocks_to_process.append((stock_code, stock_name))
        
        self.log_message(f"📋 需要處理的股票: {len(stocks_to_process)} 支")
        self.log_message(f"📋 已快取的股票: {len(cached_codes)} 支")
        
        all_results = cached_df.to_dict('records') if not cached_df.empty else []
        successful_count = len(cached_codes)
        
        try:
            # 批次處理
            for i in range(0, len(stocks_to_process), self.batch_size):
                batch = stocks_to_process[i:i + self.batch_size]
                batch_num = i // self.batch_size + 1
                total_batches = (len(stocks_to_process) + self.batch_size - 1) // self.batch_size
                
                self.log_message(f"\n📦 處理第 {batch_num}/{total_batches} 批")
                
                batch_results = []
                for stock_code, stock_name in batch:
                    self.log_message(f"🎯 處理 {stock_code} ({stock_name})...")
                    
                    data = self.get_stock_data_safe(stock_code)
                    
                    if data:
                        # 使用提供的中文名稱
                        if not data['name'] or len(data['name']) < 2:
                            data['name'] = stock_name
                        
                        batch_results.append(data)
                        all_results.append(data)
                        successful_count += 1
                        self.log_message(f"✅ 成功獲取 {stock_code} 數據")
                    else:
                        self.log_message(f"❌ 跳過 {stock_code}")
                    
                    # 請求之間的延遲
                    time.sleep(self.request_delay + random.uniform(2, 5))
                
                # 每批次後保存到快取
                if batch_results:
                    self.save_to_cache(all_results)
                
                # 批次之間的等待
                if i + self.batch_size < len(stocks_to_process):
                    self.log_message(f"⏳ 等待 {self.sleep_time} 秒後處理下一批...")
                    time.sleep(self.sleep_time)
            
            # 處理完成
            if all_results:
                df = pd.DataFrame(all_results)
                
                # 數據清理
                for col in ['ROE', 'EPS', '年營收成長率', '月營收成長率']:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                
                # 移除重複項
                df = df.drop_duplicates(subset=['stock_code'], keep='last')
                
                # 保存最終結果
                df.to_csv(self.final_file, index=False, encoding='utf-8-sig')
                
                self.generate_report(df)
                self.log_message(f"🎉 爬取完成！數據已保存到: {os.path.basename(self.final_file)}")
                
                return True
            else:
                self.log_message("❌ 沒有獲取到任何新數據")
                return False
                
        except KeyboardInterrupt:
            self.log_message("\n⏹️ 程式被使用者中斷")
            if all_results:
                df = pd.DataFrame(all_results)
                df.to_csv(f"interrupted_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", 
                         index=False, encoding='utf-8-sig')
                self.log_message("💾 已保存中斷前的數據")
            return False
        except Exception as e:
            self.log_message(f"❌ 爬取過程中發生錯誤: {str(e)}")
            return False
    
    def generate_report(self, df):
        """生成報告"""
        self.log_message("\n📊 數據統計報告:")
        self.log_message(f"總股票數: {len(df)}")
        
        # 統計有效數據
        valid_roe = df[df['ROE'] > 0]
        valid_eps = df[df['EPS'] > 0]
        
        self.log_message(f"有效 ROE 數據: {len(valid_roe)} 支 ({len(valid_roe)/len(df)*100:.1f}%)")
        self.log_message(f"有效 EPS 數據: {len(valid_eps)} 支 ({len(valid_eps)/len(df)*100:.1f}%)")
        
        if len(valid_roe) > 0:
            self.log_message(f"ROE 範圍: {valid_roe['ROE'].min():.2f}% ~ {valid_roe['ROE'].max():.2f}%")
        if len(valid_eps) > 0:
            self.log_message(f"EPS 範圍: {valid_eps['EPS'].min():.2f} ~ {valid_eps['EPS'].max():.2f}")
        
        # 優質股票
        quality_stocks = df[
            (df['ROE'] > 15) & 
            (df['EPS'] > 0) & 
            (df['年營收成長率'] > 10)
        ]
        
        self.log_message(f"🏆 優質股票 (ROE>15%, EPS>0, 年成長>10%): {len(quality_stocks)} 支")
        
        if len(quality_stocks) > 0:
            top3 = quality_stocks.nlargest(3, 'ROE')
            self.log_message("前3名優質股票:")
            for _, row in top3.iterrows():
                self.log_message(f"  {row['stock_code']} {row['name']}: ROE={row['ROE']:.2f}%, EPS={row['EPS']:.2f}")
    
    def create_sample_with_real_data(self):
        """使用真實數據創建示例，如果爬取失敗則使用假數據"""
        self.log_message("🎯 嘗試創建包含真實數據的示例文件...")
        
        # 首先嘗試爬取幾支主要股票
        sample_stocks = [
            ('2330.TW', '台積電'),
            ('2317.TW', '鴻海'),
            ('2891.TW', '中信金')
        ]
        
        real_data = []
        for stock_code, stock_name in sample_stocks:
            self.log_message(f"嘗試獲取 {stock_code} 的真實數據...")
            data = self.get_stock_data_safe(stock_code)
            
            if data:
                data['name'] = stock_name
                real_data.append(data)
                self.log_message(f"✅ 成功獲取 {stock_code} 真實數據")
                time.sleep(15)  # 長時間等待避免限制
            else:
                self.log_message(f"❌ 無法獲取 {stock_code} 真實數據")
            
            if len(real_data) >= 2:  # 只要獲取到2支就足夠
                break
        
        # 如果有真實數據，與假數據結合
        if real_data:
            self.log_message(f"✅ 獲得 {len(real_data)} 支真實數據")
            
            # 補充一些假數據
            fake_data = self.generate_fake_data(count=len(self.taiwan_stocks) - len(real_data))
            all_data = real_data + fake_data
        else:
            self.log_message("⚠️ 無法獲取真實數據，使用純假數據")
            all_data = self.generate_fake_data(count=len(self.taiwan_stocks))
        
        # 保存混合數據
        df = pd.DataFrame(all_data)
        hybrid_file = os.path.join(self.processed_dir, f'hybrid_stock_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')
        df.to_csv(hybrid_file, index=False, encoding='utf-8-sig')
        
        self.log_message(f"🎉 混合數據文件已創建: {os.path.basename(hybrid_file)}")
        self.generate_report(df)
        
        return hybrid_file
    
    def generate_fake_data(self, count):
        """生成假數據"""
        fake_data = []
        np.random.seed(42)
        
        for i, (code, name) in enumerate(self.taiwan_stocks[:count]):
            fake_data.append({
                'stock_code': f"{code}.TW",
                'name': name,
                'ROE': round(np.random.normal(15, 8), 2),
                'EPS': round(np.random.normal(2, 1.5), 2),
                '年營收成長率': round(np.random.normal(10, 20), 2),
                '月營收成長率': round(np.random.normal(8, 25), 2),
                'market_cap': int(np.random.uniform(1e9, 1e12)),
                'sector': 'Technology',
                'industry': 'Semiconductors'
            })
        
        return fake_data

def main():
    """主函數"""
    print("🔧 改進版台灣股票爬蟲")
    print("=" * 50)
    
    crawler = ImprovedStockCrawler()
    
    print("\n請選擇執行模式:")
    print("1. 保守模式爬取 (推薦)")
    print("2. 創建混合數據 (真實+假數據)")
    print("3. 僅使用假數據")
    
    try:
        choice = input("\n請輸入選項 (1-3): ").strip()
        
        if choice == '1':
            crawler.crawl_stocks_conservative()
            
        elif choice == '2':
            crawler.create_sample_with_real_data()
            
        elif choice == '3':
            fake_data = crawler.generate_fake_data(len(crawler.taiwan_stocks))
            df = pd.DataFrame(fake_data)
            fake_file = os.path.join(crawler.processed_dir, f'fake_stock_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')
            df.to_csv(fake_file, index=False, encoding='utf-8-sig')
            print(f"假數據文件已創建: {os.path.basename(fake_file)}")
            crawler.generate_report(df)
            
        else:
            print("無效選項")
            
    except KeyboardInterrupt:
        print("\n程式被中斷")
    except Exception as e:
        print(f"執行錯誤: {str(e)}")

if __name__ == "__main__":
    main() 