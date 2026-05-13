import json
import os
import re
from datetime import datetime, timedelta

try:
    import FinanceDataReader as fdr
except:
    os.system("pip install FinanceDataReader -q")
    import FinanceDataReader as fdr

my_etfs = [
    '476800','0008S0','0052D0','498410','466940','498400','489030','475720',
    '474220','441680','482730','458760','088980','0086B0','352540','0089D0',
    '0098N0','0097L0','0105E0','329200','481060','0153K0','433970','0025N0','486290'
]

def main():
    print("📡 시세 수집 시작...")
    
    master_history = {}
    
    # 기존 prices.json 로드
    if os.path.exists('prices.json'):
        with open('prices.json', 'r', encoding='utf-8') as f:
            try:
                master_history = json.load(f)
            except:
                master_history = {}
    
    success = 0
    fail = []
    
    for code in my_etfs:
        try:
            start = (datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d')
            df = fdr.DataReader(code, start=start)
            
            if df.empty:
                fail.append(code)
                continue
            
            # 최근 데이터 추가
            for i in range(1, len(df)):
                date = df.index[i].strftime('%Y-%m-%d')
                if date not in master_history:
                    master_history[date] = {}
                
                master_history[date][code] = {
                    "today": int(df['Close'].iloc[i]),
                    "prev": int(df['Close'].iloc[i-1]),
                    "src": "Python"
                }
            
            success += 1
            print(f"✅ {code}")
            
        except Exception as e:
            fail.append(code)
            print(f"⚠️ {code}: {str(e)[:50]}")
    
    # 오래된 데이터 제거 (35일 유지)
    limit = (datetime.now() - timedelta(days=35)).strftime('%Y-%m-%d')
    cleaned = {d: v for d, v in master_history.items() if d >= limit}
    sorted_data = dict(sorted(cleaned.items(), reverse=True))
    
    # prices.json 저장
    with open('prices.json', 'w', encoding='utf-8') as f:
        json.dump(sorted_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 완료: {success}/{len(my_etfs)}종목")
    print(f"📅 최신: {list(sorted_data.keys())[0] if sorted_data else 'N/A'}")

if __name__ == '__main__':
    main()
