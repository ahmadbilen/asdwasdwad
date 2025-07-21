
                
 #!/usr/bin/env python3
import subprocess
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

class CommandRunnerHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # URL'den parametreleri al
            parsed_path = urlparse(self.path)
            query_params = parse_qs(parsed_path.query)
            
            # IP ve port parametrelerini al
            ip = query_params.get('ip', [''])[0]
            port = query_params.get('port', [''])[0]
            
            self.send_response(200)
            self.send_header('Content-type', 'text/plain; charset=utf-8')
            self.end_headers()
            
            if ip and port:
                # main.py kontrolü
                if not os.path.exists('main.py'):
                    response = "HATA: main.py dosyası bulunamadı!\n"
                    response += f"Mevcut dizin: {os.getcwd()}\n"
                    response += f"Dizindeki dosyalar: {os.listdir('.')}"
                else:
                    # Komutu basit şekilde çalıştır
                    cmd_string = f"python3 start.py vse {ip}:{port} 1 30"
                    
                    # Shell=True ile çalıştır
                    result = subprocess.run(cmd_string, 
                                          shell=True,
                                          capture_output=True, 
                                          text=True, 
                                          timeout=30)
                    
                    response = f"Çalıştırılan komut: {cmd_string}\n"
                    response += "="*50 + "\n"
                    
                    if result.stdout:
                        response += result.stdout
                    else:
                        response += "Çıktı yok\n"
                    
                    if result.stderr:
                        response += f"\nHata çıktısı:\n{result.stderr}"
                    
                    response += f"\n\nÇıkış kodu: {result.returncode}"
            else:
                response = "HATA: IP ve port parametreleri gerekli!\n"
                response += "Kullanım: http://localhost:8080?ip=1.1.1.1&port=80"
            
            self.wfile.write(response.encode('utf-8'))
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'text/plain; charset=utf-8')
            self.end_headers()
            error_msg = f"Sunucu hatası: {type(e).__name__}: {str(e)}\n"
            import traceback
            error_msg += traceback.format_exc()
            self.wfile.write(error_msg.encode('utf-8'))
    
    def log_message(self, format, *args):
        pass  # Logları gizle

def run_server(port=8080):
    httpd = HTTPServer(('', port), CommandRunnerHandler)
    print(f"Sunucu başlatıldı: http://localhost:{port}")
    print(f"Test: http://localhost:{port}?ip=1.1.1.1&port=80")
    print(f"Çalışma dizini: {os.getcwd()}")
    
    if os.path.exists('main.py'):
        print("✓ main.py mevcut")
    else:
        print("✗ main.py bulunamadı!")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nSunucu kapatılıyor...")

if __name__ == '__main__':
    run_server()
