import json
from datetime import datetime

# 테스트용 간단한 코드
data = {
    datetime.now().strftime('%Y-%m-%d'): {
        "476800": {"today": 10000, "prev": 9900, "src": "Python"}
    }
}

with open('prices.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("✅ 테스트 완료!")
