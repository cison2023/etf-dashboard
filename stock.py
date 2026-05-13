import FinanceDataReader as fdr
import json, os, re, sys, threading, time
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler

save_folder = r"C:\Users\SON\Desktop\주식프로젝트"
html_file   = os.path.join(save_folder, "ETF_index_Ver3_1.html")
save_path   = os.path.join(save_folder, "prices.json")
KEEP_DAYS   = 35
SERVER_PORT = 9877

my_etfs = [
    '476800','0008S0','0052D0','498410','466940','498400','489030','475720',
    '474220','441680','482730','458760','088980','0086B0','352540','0089D0',
    '0098N0','0097L0','0105E0','329200','481060','0153K0','433970','0025N0','486290'
]

# ═════════════════════════════════════════════════════════
# 시세 업데이트 함수
# ═════════════════════════════════════════════════════════
def run_update():
    """시세 데이터를 수집하고 HTML 파일에 자동 반영"""
    master_history = {}
    if os.path.exists(save_path):
        with open(save_path, 'r', encoding='utf-8') as f:
            try:
                raw = json.load(f)
                master_history = {d: v for d, v in raw.items()
                                  if re.match(r'^\d{4}-\d{2}-\d{2}$', str(d))}
            except:
                master_history = {}

    print(f"[{datetime.now().strftime('%H:%M:%S')}] 📡 시세 업데이트 시작 (기존: {len(master_history)}일)")
    success_cnt, fail_list = 0, []

    for code in my_etfs:
        try:
            start_dt = (datetime.now() - timedelta(days=50)).strftime('%Y-%m-%d')
            df = fdr.DataReader(code, start=start_dt)
            if df.empty:
                fail_list.append(code)
                continue
            
            for i in range(1, len(df)):
                date_str = df.index[i].strftime('%Y-%m-%d')
                if date_str not in master_history:
                    master_history[date_str] = {}
                master_history[date_str][code] = {
                    "today": int(df['Close'].iloc[i]),
                    "prev":  int(df['Close'].iloc[i-1]),
                    "src":   "Python"
                }
            success_cnt += 1
            print(f"  ✅ {code}")
        except Exception as e:
            fail_list.append(code)
            print(f"  ⚠️  {code}: {str(e)[:30]}")

    # 오래된 데이터 정리
    limit_date = (datetime.now() - timedelta(days=KEEP_DAYS)).strftime('%Y-%m-%d')
    sorted_history = dict(sorted({d: v for d, v in master_history.items() if d >= limit_date}.items(), reverse=True))

    # prices.json 저장
    with open(save_path, 'w', encoding='utf-8') as f:
        json.dump(sorted_history, f, ensure_ascii=False, indent=2)

    # HTML 파일의 PYTHON_PRICES_DATA 블록 자동 업데이트
    html_updated = False
    if os.path.exists(html_file):
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        generated_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        new_block = (
            f'<!-- ★ 아래 블록은 stock.py가 자동으로 덮어씁니다. 수동 편집 금지 -->\n'
            f'<script id="py-prices-block">\n'
            f'// stock.py 업데이트: {generated_at}\n'
            f'window.PYTHON_PRICES_DATA = {json.dumps(sorted_history, ensure_ascii=False)};\n'
            f'</script>'
        )
        
        pattern = r'<!-- ★ 아래 블록은 stock\.py가 자동으로 덮어씁니다\. 수동 편집 금지 -->.*?</script>'
        updated, n = re.subn(pattern, new_block, html_content, flags=re.DOTALL)
        
        if n > 0:
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(updated)
            html_updated = True
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 🌐 HTML 시세 블록 업데이트 완료")

    dates = list(sorted_history.keys())
    result = {
        "ok": True,
        "success": success_cnt,
        "total": len(my_etfs),
        "fail": fail_list,
        "newest": dates[0] if dates else 'N/A',
        "oldest": dates[-1] if dates else 'N/A',
        "days": len(sorted_history),
        "html_updated": html_updated,
        "time": datetime.now().strftime('%H:%M:%S')
    }
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ 업데이트 완료: {success_cnt}/{len(my_etfs)}종목 · {dates[0] if dates else 'N/A'}")
    return result

# ═════════════════════════════════════════════════════════
# HTTP 서버 (HTML에서 요청받아 시세 업데이트)
# ═════════════════════════════════════════════════════════
class PriceHandler(BaseHTTPRequestHandler):
    """HTTP 요청 처리"""
    
    def do_OPTIONS(self):
        self.send_response(200)
        self._set_cors_headers()
        self.end_headers()

    def do_GET(self):
        if self.path == '/status':
            self.send_response(200)
            self._set_cors_headers()
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(b'{"ok":true}')
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        """HTML에서 POST 요청 받아서 시세 업데이트 실행"""
        if self.path == '/update':
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(content_length)
                
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 📩 업데이트 요청 수신")
                
                # 시세 업데이트 실행
                result = run_update()
                
                # JSON 응답
                response = json.dumps(result, ensure_ascii=False).encode('utf-8')
                self.send_response(200)
                self._set_cors_headers()
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.send_header('Content-Length', len(response))
                self.end_headers()
                self.wfile.write(response)
                
            except Exception as e:
                error_msg = str(e)
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ 오류: {error_msg}")
                response = json.dumps({
                    "ok": False,
                    "error": error_msg
                }, ensure_ascii=False).encode('utf-8')
                self.send_response(500)
                self._set_cors_headers()
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(response)
        else:
            self.send_response(404)
            self.end_headers()

    def _set_cors_headers(self):
        """CORS 헤더 설정"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def log_message(self, format, *args):
        """로그 출력"""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {format%args}")

# ═════════════════════════════════════════════════════════
# 서버 실행
# ═════════════════════════════════════════════════════════
def run_server():
    """HTTP 서버 시작"""
    server = HTTPServer(('localhost', SERVER_PORT), PriceHandler)
    print(f"\n{'='*60}")
    print(f"🖥️  시세 서버 실행 중 — http://localhost:{SERVER_PORT}")
    print(f"이제 HTML의 '시세 업데이트 실행' 버튼을 클릭하면 자동 반영됩니다")
    print(f"서버 종료: Ctrl+C 입력")
    print(f"{'='*60}\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\n[서버 종료]")
        server.shutdown()

# ═════════════════════════════════════════════════════════
# 메인 실행
# ═════════════════════════════════════════════════════════
if __name__ == '__main__':
    if '--server' in sys.argv:
        # 서버 모드: 항상 대기 상태
        run_server()
    else:
        # 단순 업데이트 모드 (GitHub Actions용)
        print(f"\n{'='*60}")
        print(f"🚀 주식 시세 업데이트 스크립트")
        print(f"{'='*60}\n")
        result = run_update()
        print(f"\n{'='*60}")
        print(f"📊 업데이트 결과")
        print(f"  ✅ 성공: {result['success']}/{result['total']} 종목")
        print(f"  📅 범위: {result['oldest']} ~ {result['newest']}")
        print(f"  📦 보관: {result['days']}일치")
        if result['fail']:
            print(f"  ⚠️  실패: {', '.join(result['fail'])}")
        print(f"{'='*60}\n")
