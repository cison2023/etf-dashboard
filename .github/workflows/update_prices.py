import json
import os
import yfinance as yf
from datetime import datetime, timedelta

codes = [
    '476800.KS', '0008S0.KS', '0052D0.KS', '498410.KS', '466940.KS',
    '498400.KS', '489030.KS', '475720.KS', '474220.KS', '441680.KS',
    '482730.KS', '458760.KS', '088980.KS', '0086B0.KS', '352540.KS',
    '0089D0.KS', '0098N0.KS', '0097L0.KS', '0105E0.KS', '329200.KS',
    '481060.KS', '0153K0.KS', '433970.KS', '0025N0.KS', '486290.KS'
]

data = {}

# 기존 데이터 로드
try:
    with open('prices.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
except FileNotFoundError:
    print("새 파일 생성 중...")
except json.JSONDecodeError:
    print("⚠️ prices.json 파싱 오류, 초기화")
    data = {}

# 시세 데이터 수집
for code in codes:
    try:
        df = yf.download(code, period='60d', progress=False, quiet=True)
        
        if df.empty:
            print(f'⚠️ {code} - 데이터 없음')
            continue
        
        for i in range(1, len(df)):
            date = df.index[i].strftime('%Y-%m-%d')
            if date not in data:
                data[date] = {}
            
            ticker = code.split('.')[0]
            data[date][ticker] = {
                'today': int(df['Close'].iloc[i]),
                'prev': int(df['Close'].iloc[i-1]),
                'src': 'Python'
            }
        
        print(f'✅ {code}')
    
    except Exception as e:
        print(f'⚠️ {code} - {str(e)[:50]}')

# 35일 이내 데이터만 유지
limit_date = (datetime.now() - timedelta(days=35)).strftime('%Y-%m-%d')
result = dict(sorted(
    {d: v for d, v in data.items() if d >= limit_date}.items(),
    reverse=True
))

# 결과 저장
try:
    with open('prices.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f'\n✅ 완료: {len(result)}일치 저장됨')
except Exception as e:
    print(f'❌ 저장 실패: {e}')
    exit(1)
