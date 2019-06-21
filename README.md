# CNLAB2019

## 環境

1. 下載Mininet VM
2. 下載code

## example

```
# start SDN controller
PYTHONPATH=. ryu-manager final_ryu.py 

# start mininet and experiment controller 
python3 net.py -n 10 -o tmp

# run experients
> server h2
> agent h1
> client h3 h2
> attacker h4 h10 h2

# see outputs
agent:    tail -f tmp/h1.out
server:   tail -f tmp/h2.out
client:   tail -f tmp/h3.out
attacker: tail -f tmp/h4.out
```

## 細節

### controller

* controller會檢查目的地為被保護server的tcp封包，若第一個封包的client puzzle通過檢查，
  就新增一條rule，之後同(ip, port) -> (ip, port)的tcp封包就正常移動，不轉送controller檢查
* 由agent告知與server相關的訊息，或是刪除rule等等

### net.py

* 可以統一執行server.py，agent.py，client.py和attacker.py
* server [host]
* agent [host]
* client [client_host] [server_host]
* attacker [attacker_host_start] [attacker_host_end] [server_host]

### agent.py

* 要使用client puzzle服務的server向agent註冊，會和agent建立tcp連線管理server和client的連線狀態
* server也使用client puzzle向agent溝通
* agent會適度檢查server傳來的訊息合法性

### client_auto.py

* 會定期的向server傳訊息
* 可用來偵測在attacker攻擊時是否仍有辦法和server連線

### server.py

* 會向agent發出註冊申請，註冊後成為被client puzzle保護的server
* 本身是echo server，預設聽在port 6666
* 可以打指令向agent發送請求:
	1.	open port:X, Y
	
		X: port number, Y: 可允許最大連線數
	2.	close port:X
	3.	df, src_ip, src_port, dst_port
		向agent刪除該連線，agent檢查合法後會轉送給controller刪除該條rule
