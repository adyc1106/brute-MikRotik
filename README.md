#Note 1
Option command, python3 wordlist.py -d 6 -c 2000 -o wordlist.txt
==| Penjelasan |==
-d 6               { Jumlah digit yang akan digenerate }
-c 2000            { Jumlah kemungkinan yang akan digenerate yaitu 2000 kemungkinan }
-o wordlist.txt    { Output hasil generate kemungkinan, akan di simpan pada file dengan nama wordlist.txt }

#Note 2
Command => python3 brute.py 192.168.1.1 -m api -p 8278 -u admin -w wordlist.txt -t 5
==| Penjelasan |==

192.168.1.1      => silahkan di sesuaikan dengan Gateway atau ip mikrotik target
-m 8278          => Port api mikrotik default 8278, jika port api mirkotik di custome silahkan di sesuaikan
-u admin         => Option untuk username yang akan digunakan untuk percobaan login ke mikrotik
-w wordlist.txt  => Nama file wordlist atau file yang berisi kemungkinan password yang digunakan target
-U Username.txt  => Jika username menggunakan wordlist 
-t 5             => Value lenght Thread (1 - 10).
