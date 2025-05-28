import pandas as pd
import time
from datetime import datetime, timedelta
import os
import random
import requests
from collections import deque
import json
import yfinance as yf

class StockDataCrawler:
    def __init__(self):
        self.batch_size = 1  # 每次只處理一支股票
        self.sleep_time = 10  # 批次之間的等待時間（10秒）
        self.request_delay = 5  # 請求之間的延遲時間（5秒）
        self.max_retries = 3  # 最大重試次數
        self.retry_delay = 60  # 重試等待時間（1分鐘）
        
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
        self.valid_stocks_file = os.path.join(self.raw_dir, 'valid_stocks.txt')
        self.failed_stocks_file = os.path.join(self.raw_dir, 'failed_stocks.txt')
        self.interim_file = os.path.join(self.raw_dir, f'interim_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')
        self.final_file = os.path.join(self.processed_dir, f'stock_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')
        self.log_file = os.path.join(self.logs_dir, f'crawler_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
        
        # 設定請求限制追蹤
        self.get_minute_requests = deque(maxlen=60)  # GET 請求每分鐘限制
        self.get_hour_requests = deque(maxlen=360)   # GET 請求每小時限制
        self.get_day_requests = deque(maxlen=8000)   # GET 請求每天限制
        
        # 設定請求標頭
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        # 初始化或讀取有效的股票代碼
        if not os.path.exists(self.valid_stocks_file):
            self.generate_valid_stocks()
        else:
            print(f"從 {self.valid_stocks_file} 讀取有效的股票代碼")
    
    def log_message(self, message):
        """記錄訊息到日誌檔案"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] {message}\n"
        
        # 同時輸出到控制台和日誌檔案
        print(message)
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)
    
    def generate_valid_stocks(self):
        """生成可能的股票代碼並保存到文件"""
        self.log_message("生成股票代碼...")
        valid_stocks = []
        
        # 生成 0000-9999 的股票代碼
        for i in range(10000):
            stock_code = f"{i:04d}.TW"
            valid_stocks.append(stock_code)
        
        # 保存到文件
        with open(self.valid_stocks_file, 'w') as f:
            for stock in valid_stocks:
                f.write(f"{stock}\n")
        
        self.log_message(f"已生成 {len(valid_stocks)} 個股票代碼並保存到 {self.valid_stocks_file}")
    
    def track_request(self):
        """追蹤請求"""
        now = time.time()
        self.get_minute_requests.append(now)
        self.get_hour_requests.append(now)
        self.get_day_requests.append(now)
    
    def get_rate_limits(self):
        """獲取當前的請求限制狀態"""
        now = time.time()
        minute_ago = now - 60
        hour_ago = now - 3600
        day_ago = now - 86400
        
        get_minute = len([t for t in self.get_minute_requests if t > minute_ago])
        get_hour = len([t for t in self.get_hour_requests if t > hour_ago])
        get_day = len([t for t in self.get_day_requests if t > day_ago])
        
        return {
            'get': {
                'minute': {'current': get_minute, 'limit': 60, 'remaining': 60 - get_minute},
                'hour': {'current': get_hour, 'limit': 360, 'remaining': 360 - get_hour},
                'day': {'current': get_day, 'limit': 8000, 'remaining': 8000 - get_day}
            }
        }
    
    def print_rate_limits(self):
        """顯示當前的請求限制狀態"""
        limits = self.get_rate_limits()
        message = "\n當前請求限制狀態:\nGET 請求限制:\n"
        message += f"  每分鐘: {limits['get']['minute']['current']}/{limits['get']['minute']['limit']} (剩餘: {limits['get']['minute']['remaining']})\n"
        message += f"  每小時: {limits['get']['hour']['current']}/{limits['get']['hour']['limit']} (剩餘: {limits['get']['hour']['remaining']})\n"
        message += f"  每天: {limits['get']['day']['current']}/{limits['get']['day']['limit']} (剩餘: {limits['get']['day']['remaining']})"
        self.log_message(message)
    
    def get_stock_data(self, stock_code):
        """獲取股票數據"""
        for retry in range(self.max_retries):
            try:
                self.track_request()
                self.print_rate_limits()
                
                # 檢查請求限制
                limits = self.get_rate_limits()
                if limits['get']['minute']['remaining'] <= 0:
                    self.log_message("達到每分鐘請求限制，等待60秒...")
                    time.sleep(60)
                elif limits['get']['hour']['remaining'] <= 0:
                    self.log_message("達到每小時請求限制，等待3600秒...")
                    time.sleep(3600)
                elif limits['get']['day']['remaining'] <= 0:
                    self.log_message("達到每天請求限制，等待86400秒...")
                    time.sleep(86400)
                
                # 使用 yfinance 獲取股票數據
                stock = yf.Ticker(stock_code)
                info = stock.info
                
                # 獲取歷史營收數據
                financials = stock.financials
                if financials is not None and not financials.empty:
                    # 計算年營收成長率
                    current_year_revenue = financials.iloc[0, 0]  # 假設第一行是總營收
                    last_year_revenue = financials.iloc[0, 1]  # 假設第二行是去年營收
                    annual_revenue_growth = (current_year_revenue / last_year_revenue - 1) * 100 if last_year_revenue != 0 else 0
                    
                    # 計算月營收成長率
                    monthly_data = stock.history(period="13mo")  # 獲取近13個月數據
                    if not monthly_data.empty:
                        current_month_revenue = monthly_data['Close'].iloc[-1]
                        last_year_month_revenue = monthly_data['Close'].iloc[-13]
                        monthly_revenue_growth = (current_month_revenue / last_year_month_revenue - 1) * 100 if last_year_month_revenue != 0 else 0
                    else:
                        monthly_revenue_growth = 0
                else:
                    annual_revenue_growth = 0
                    monthly_revenue_growth = 0
                
                # 整理數據
                data = {
                    'stock_code': stock_code,
                    'name': info.get('longName', ''),
                    'ROE': info.get('returnOnEquity', 0) * 100,
                    'EPS': info.get('trailingEps', 0),
                    '年營收成長率': annual_revenue_growth,
                    '月營收成長率': monthly_revenue_growth
                }
                
                self.log_message(f"成功更新 {stock_code}")
                return data
            
            except Exception as e:
                self.log_message(f"更新 {stock_code} 時發生錯誤: {str(e)}")
                if retry < self.max_retries - 1:
                    wait_time = self.retry_delay * (retry + 1)
                    self.log_message(f"等待 {wait_time} 秒後重試... (第 {retry + 1} 次重試)")
                    time.sleep(wait_time)
                else:
                    self.log_message(f"已達到最大重試次數，跳過 {stock_code}")
                    return None
    
    def process_batch(self, batch):
        """處理一批股票"""
        results = []
        for stock_code in batch:
            self.log_message(f"\n正在更新 {stock_code}...")
            data = self.get_stock_data(stock_code)
            if data:
                results.append(data)
            time.sleep(self.request_delay + random.uniform(0.1, 0.5))
        self.save_results(results)
    
    def save_results(self, results):
        """保存結果到CSV文件"""
        if not results:
            return
            
        df = pd.DataFrame(results)
        
        # 如果文件存在，則追加；否則創建新文件
        if os.path.exists(self.interim_file):
            df.to_csv(self.interim_file, mode='a', header=False, index=False, encoding='utf-8-sig')
        else:
            df.to_csv(self.interim_file, index=False, encoding='utf-8-sig')
        
        self.log_message(f"已保存 {len(results)} 筆數據到 {self.interim_file}")
    
    def update_all_stocks(self):
        """更新所有股票數據"""
        self.log_message("開始更新股票數據...")
        self.log_message("這個過程可能需要較長時間，程式會定期保存中間結果")
        self.log_message("您可以隨時按 Ctrl+C 中斷程式，已處理的數據會被保存")
        
        try:
            # 讀取有效的股票代碼
            with open(self.valid_stocks_file, 'r') as f:
                valid_stocks = [line.strip() for line in f.readlines()]
            
            self.log_message(f"找到 {len(valid_stocks)} 支股票")
            
            # 批次處理
            total_batches = (len(valid_stocks) + self.batch_size - 1) // self.batch_size
            
            for i in range(0, len(valid_stocks), self.batch_size):
                batch = valid_stocks[i:i + self.batch_size]
                batch_num = i // self.batch_size + 1
                self.log_message(f"\n處理第 {batch_num}/{total_batches} 批，股票代碼 {batch[0]} 到 {batch[-1]}")
                
                self.process_batch(batch)
                
                # 批次之間的等待
                if i + self.batch_size < len(valid_stocks):
                    self.log_message(f"等待 {self.sleep_time} 秒後處理下一批...")
                    time.sleep(self.sleep_time)
            
            # 處理完成後，將結果文件重命名為最終文件
            if os.path.exists(self.interim_file):
                os.rename(self.interim_file, self.final_file)
                self.log_message(f"\n所有數據已保存到 {self.final_file}")
        
        except KeyboardInterrupt:
            self.log_message("\n程式被使用者中斷")
            if os.path.exists(self.interim_file):
                self.log_message(f"已處理的數據已保存到 {self.interim_file}")
        except Exception as e:
            self.log_message(f"更新股票數據時發生錯誤: {str(e)}")
    
    def scheduled_update(self):
        """排程更新任務"""
        print(f"\n開始排程更新 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.update_all_stocks()

def main():
    crawler = StockDataCrawler()
    
    # 執行一次完整的股票數據更新
    print("\n開始更新股票數據...")
    crawler.update_all_stocks()
    
    print("\n程式執行完成")

if __name__ == "__main__":
    main() 