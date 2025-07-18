#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import random
import string
import argparse
from datetime import datetime

def print_banner():
    print("""
    ============================================
         RANDOM WORDLIST GENERATOR
         For educational purposes only
    ============================================
    WARNING: Use only for legal activities!
    Unauthorized access is illegal.
    ============================================
    """)

def generate_wordlist(digits, count, output_file=None, chars=None):
    """Generate random wordlist with specified digits"""
    if chars is None:
        chars = string.ascii_lowercase + string.digits
    
    wordlist = []
    for _ in range(count):
        word = ''.join(random.choice(chars) for _ in range(digits))
        wordlist.append(word)
    
    if output_file:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(output_file, 'w') as f:
            f.write(f"# Wordlist generated at {timestamp}\n")
            f.write(f"# Config: {digits} digits, {count} combinations\n")
            f.write("\n".join(wordlist))
        print(f"\n[+] Wordlist saved to {output_file} ({count} combinations)")
    
    return wordlist

def main():
    print_banner()
    
    parser = argparse.ArgumentParser(description='Generate random wordlist')
    parser.add_argument('-d', '--digits', type=int, help='Number of digits per word')
    parser.add_argument('-c', '--count', type=int, default=100, help='Number of words to generate')
    parser.add_argument('-o', '--output', help='Output file name')
    parser.add_argument('--uppercase', action='store_true', help='Include uppercase letters')
    parser.add_argument('--no-digits', action='store_true', help='Exclude digits')
    parser.add_argument('--special', action='store_true', help='Include special characters')
    
    args = parser.parse_args()
    
    if args.digits is None:
        try:
            args.digits = int(input("Enter number of digits per word: "))
            args.count = int(input(f"Enter number of words to generate [default {args.count}]: ") or args.count)
            save_file = input("Save to file? (leave blank to skip): ")
            if save_file:
                args.output = save_file
        except ValueError:
            print("\n[!] Error: Please enter valid numbers")
            return
    
    chars = string.ascii_lowercase
    if args.uppercase:
        chars += string.ascii_uppercase
    if not args.no_digits:
        chars += string.digits
    if args.special:
        chars += string.punctuation
    
    print(f"\n[+] Generating {args.count} {args.digits}-character words...")
    wordlist = generate_wordlist(args.digits, args.count, args.output, chars)
    
    print("\nSample words:")
    for word in wordlist[:10]:
        print(f"  {word}")
    if len(wordlist) > 10:
        print(f"  ... and {len(wordlist)-10} more")

if __name__ == "__main__":
    main()
