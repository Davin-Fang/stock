#!/usr/bin/env python3
"""測試股票列表載入"""

try:
    from hybrid_real_crawler import HybridRealCrawler
    
    print("🔧 初始化爬蟲...")
    crawler = HybridRealCrawler()
    
    print(f"📊 載入股票數量: {len(crawler.taiwan_stocks)}")
    print(f"📄 前5支股票: {crawler.taiwan_stocks[:5]}")
    print(f"📄 後5支股票: {crawler.taiwan_stocks[-5:]}")
    
    # 檢查是否有重複
    codes = [stock[0] for stock in crawler.taiwan_stocks]
    unique_codes = set(codes)
    print(f"🔍 唯一股票代碼數: {len(unique_codes)}")
    
    if len(codes) != len(unique_codes):
        print("⚠️ 發現重複的股票代碼")
    else:
        print("✅ 沒有重複的股票代碼")
    
    print("✅ 股票列表載入測試完成")
    
except Exception as e:
    print(f"❌ 錯誤: {e}")
    import traceback
    traceback.print_exc() 