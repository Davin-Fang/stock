#!/usr/bin/env python3
"""
TWSE 股價數據下載器
預先下載台灣股票歷史價格數據並存儲在本地數據庫
"""

import pandas as pd
import requests
import time
import os
from datetime import datetime, timedelta
import json
import glob

class TWSEDataDownloader:
    def __init__(self):
        self.data_dir = 'data/stock_prices'
        self.logs_dir = 'data/logs'
        
        # 創建目錄
        for directory in [self.data_dir, self.logs_dir]:
            os.makedirs(directory, exist_ok=True)
        
        self.log_file = os.path.join(self.logs_dir, f'twse_download_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
        
        # 載入股票代碼列表
        self.stock_codes = self.load_stock_codes()
    
    def load_stock_codes(self):
        """載入股票代碼列表"""
        # 從現有數據文件中提取股票代碼
        data_patterns = [
            'data/processed/fixed_real_stock_data_*.csv',
            'data/processed/hybrid_real_stock_data_*.csv',
            'data/processed/taiwan_all_stocks_complete_*.csv'
        ]
        
        for pattern in data_patterns:
            files = glob.glob(pattern)
            if files:
                latest_file = max(files, key=os.path.getctime)
                try:
                    df = pd.read_csv(latest_file)
                    if 'stock_code' in df.columns:
                        # 提取股票代碼，去除.TW後綴
                        codes = df['stock_code'].str.replace('.TW', '').unique().tolist()
                        self.log_message(f"✅ 從 {latest_file} 載入 {len(codes)} 個股票代碼")
                        return codes
                except Exception as e:
                    self.log_message(f"❌ 讀取 {latest_file} 失敗: {str(e)}")
        
        # 如果無法載入，使用預設的主要股票代碼
        default_codes = [
            '2330', '2317', '2454', '2891', '2882', '2881', '2412', '2002', '1301',
            '2308', '2382', '2357', '3711', '2303', '2327', '2912', '1216', '2105',
            '2207', '3008', '2395', '2379', '1303', '2886', '2884', '6505', '0050',
            '0056', '2409', '2408', '2474', '3034', '2324', '2301', '1102', '2880'
        ]
        self.log_message(f"⚠️ 使用預設股票代碼列表: {len(default_codes)} 個")
        return default_codes
    
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
    
    def download_stock_data(self, stock_code, years=3):
        """下載單一股票的歷史數據"""
        try:
            self.log_message(f"📊 開始下載 {stock_code} 的數據...")
            
            # 計算日期範圍
            end_date = datetime.now()
            start_date = end_date - timedelta(days=years * 365)
            
            all_data = []
            current_date = start_date
            
            # 按月份下載數據
            while current_date <= end_date:
                year = current_date.year
                month = current_date.month
                
                # TWSE API URL
                url = "https://www.twse.com.tw/exchangeReport/STOCK_DAY"
                params = {
                    'response': 'json',
                    'date': f"{year}{month:02d}01",
                    'stockNo': stock_code
                }
                
                try:
                    response = requests.get(url, params=params, timeout=15)
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        if 'data' in data and data['data']:
                            for row in data['data']:
                                try:
                                    # 解析數據
                                    date_parts = row[0].split('/')
                                    if len(date_parts) == 3:
                                        # 民國年轉西元年
                                        year_ad = int(date_parts[0]) + 1911
                                        month_num = int(date_parts[1])
                                        day_num = int(date_parts[2])
                                        
                                        trade_date = datetime(year_ad, month_num, day_num)
                                        
                                        # 解析價格數據
                                        volume = int(row[1].replace(',', '')) if row[1] != '--' else 0
                                        open_price = float(row[3].replace(',', '')) if row[3] != '--' else 0
                                        high_price = float(row[4].replace(',', '')) if row[4] != '--' else 0
                                        low_price = float(row[5].replace(',', '')) if row[5] != '--' else 0
                                        close_price = float(row[6].replace(',', '')) if row[6] != '--' else 0
                                        
                                        if close_price > 0:  # 只保留有效數據
                                            all_data.append({
                                                'Date': trade_date,
                                                'Open': open_price,
                                                'High': high_price,
                                                'Low': low_price,
                                                'Close': close_price,
                                                'Volume': volume
                                            })
                                
                                except (ValueError, IndexError) as e:
                                    continue
                        
                        # 延遲避免請求過快
                        time.sleep(2)
                    
                    else:
                        self.log_message(f"⚠️ {stock_code} {year}/{month} HTTP錯誤: {response.status_code}")
                
                except requests.RequestException as e:
                    self.log_message(f"⚠️ {stock_code} {year}/{month} 請求失敗: {str(e)}")
                
                # 移到下個月
                if month == 12:
                    current_date = datetime(year + 1, 1, 1)
                else:
                    current_date = datetime(year, month + 1, 1)
            
            # 保存數據
            if all_data:
                df = pd.DataFrame(all_data)
                df = df.sort_values('Date').reset_index(drop=True)
                
                # 保存到文件
                filename = os.path.join(self.data_dir, f'{stock_code}_price_data.csv')
                df.to_csv(filename, index=False, encoding='utf-8-sig')
                
                self.log_message(f"✅ {stock_code} 下載完成: {len(df)} 筆數據，保存至 {filename}")
                return True
            else:
                self.log_message(f"❌ {stock_code} 沒有獲取到任何數據")
                return False
        
        except Exception as e:
            self.log_message(f"❌ {stock_code} 下載失敗: {str(e)}")
            return False
    
    def download_all_stocks(self):
        """下載所有股票數據"""
        self.log_message("🚀 開始批量下載TWSE股票數據...")
        self.log_message(f"📊 目標股票數: {len(self.stock_codes)}")
        
        success_count = 0
        failed_stocks = []
        
        try:
            for i, stock_code in enumerate(self.stock_codes, 1):
                self.log_message(f"\n📈 處理 {i}/{len(self.stock_codes)}: {stock_code}")
                
                # 檢查是否已存在
                existing_file = os.path.join(self.data_dir, f'{stock_code}_price_data.csv')
                if os.path.exists(existing_file):
                    # 檢查文件是否是最近的（7天內）
                    file_time = os.path.getctime(existing_file)
                    current_time = time.time()
                    
                    if current_time - file_time < 7 * 24 * 3600:  # 7天內
                        self.log_message(f"⏭️ {stock_code} 數據已存在且較新，跳過")
                        success_count += 1
                        continue
                
                # 下載數據
                if self.download_stock_data(stock_code):
                    success_count += 1
                else:
                    failed_stocks.append(stock_code)
                
                # 每10支股票休息一下
                if i % 10 == 0:
                    self.log_message(f"⏳ 已處理 {i}/{len(self.stock_codes)}，休息5秒...")
                    time.sleep(5)
                
                # 每支股票間隔
                time.sleep(1)
            
            # 生成報告
            self.generate_download_report(success_count, failed_stocks)
            
        except KeyboardInterrupt:
            self.log_message("\n⏹️ 下載被用戶中斷")
            self.log_message(f"📊 已成功下載: {success_count} 支股票")
        except Exception as e:
            self.log_message(f"❌ 批量下載過程發生錯誤: {str(e)}")
    
    def generate_download_report(self, success_count, failed_stocks):
        """生成下載報告"""
        total_stocks = len(self.stock_codes)
        success_rate = success_count / total_stocks * 100 if total_stocks > 0 else 0
        
        self.log_message("\n📊 TWSE數據下載報告:")
        self.log_message("=" * 50)
        self.log_message(f"🎯 目標股票總數: {total_stocks}")
        self.log_message(f"✅ 成功下載: {success_count} 支 ({success_rate:.1f}%)")
        self.log_message(f"❌ 失敗股票: {len(failed_stocks)} 支")
        
        if failed_stocks:
            self.log_message(f"\n❌ 失敗股票列表:")
            for i, code in enumerate(failed_stocks[:20], 1):  # 只顯示前20個
                self.log_message(f"  {i}. {code}")
            
            if len(failed_stocks) > 20:
                self.log_message(f"  ... 還有 {len(failed_stocks) - 20} 支股票失敗")
        
        # 檢查數據庫狀態
        existing_files = glob.glob(os.path.join(self.data_dir, '*_price_data.csv'))
        self.log_message(f"\n📁 數據庫狀態:")
        self.log_message(f"  總數據文件: {len(existing_files)}")
        
        if existing_files:
            # 計算總數據量
            total_records = 0
            for file in existing_files:
                try:
                    df = pd.read_csv(file)
                    total_records += len(df)
                except:
                    pass
            
            self.log_message(f"  總交易記錄: {total_records:,} 筆")
            self.log_message(f"  平均每股: {total_records // len(existing_files):,} 筆")
        
        self.log_message("=" * 50)
    
    def get_available_stocks(self):
        """獲取可用的股票列表"""
        files = glob.glob(os.path.join(self.data_dir, '*_price_data.csv'))
        available_stocks = []
        
        for file in files:
            stock_code = os.path.basename(file).replace('_price_data.csv', '')
            try:
                df = pd.read_csv(file)
                if len(df) > 50:  # 至少要有50筆數據
                    available_stocks.append({
                        'code': stock_code,
                        'records': len(df),
                        'date_range': f"{df['Date'].min()} ~ {df['Date'].max()}"
                    })
            except:
                pass
        
        return available_stocks

def main():
    """主函數"""
    print("TWSE 股價數據下載器")
    print("=" * 50)
    print("功能：")
    print("✓ 從台灣證券交易所下載歷史股價數據")
    print("✓ 存儲在本地數據庫供快速查詢")
    print("✓ 支援批量下載和增量更新")
    print("=" * 50)
    
    downloader = TWSEDataDownloader()
    
    try:
        choice = input("\n選擇操作:\n1. 下載所有股票數據\n2. 查看可用股票\n3. 下載單一股票\n請輸入選項 (1-3): ").strip()
        
        if choice == "1":
            confirm = input(f"\n將下載 {len(downloader.stock_codes)} 支股票的數據，可能需要較長時間。是否繼續？(y/N): ").strip().lower()
            if confirm in ['y', 'yes']:
                downloader.download_all_stocks()
            else:
                print("👋 取消下載")
        
        elif choice == "2":
            available = downloader.get_available_stocks()
            if available:
                print(f"\n📊 可用股票數據 ({len(available)} 支):")
                for stock in available[:20]:  # 只顯示前20個
                    print(f"  {stock['code']}: {stock['records']} 筆記錄 ({stock['date_range']})")
                if len(available) > 20:
                    print(f"  ... 還有 {len(available) - 20} 支股票")
            else:
                print("❌ 沒有可用的股票數據")
        
        elif choice == "3":
            stock_code = input("\n請輸入股票代碼 (例如: 2330): ").strip()
            if stock_code:
                downloader.download_stock_data(stock_code)
            else:
                print("❌ 無效的股票代碼")
        
        else:
            print("❌ 無效的選項")
    
    except KeyboardInterrupt:
        print("\n👋 程式已取消")
    except Exception as e:
        print(f"\n❌ 執行錯誤: {str(e)}")

if __name__ == "__main__":
    main() 