# CNLAB2019

## 環境

1. 下載Mininet VM
2. windows照助教講義下載xterm，mac OS可用xquartz，然後ssh -Y連VM
   [link](https://www.xquartz.org)
3. 下載code

## example

1. 開兩個視窗
2. A 視窗 ./final_run.sh 0 跑Mininet
3. B 視窗 ./final_run.sh 1 跑controller
4. A: xterm h1 h2 h3
5. h3: python client.py，
6. h2: python server.py，server預設會架在port 6666，為簡單的echo server
7. h1: python agent.py，最後跑
8. 等到h2出現register和open port: 6666, 20，表示server向controller註冊成功
9. h1此時應該已經有dump file: solved_ans003.json，表示該次client puzzle已solved，press Enter
10. h1連線的dst應為h2的server，press Enter
11. h1連線成功後可以連上h2的echo server，exit可離開

## 細節

### controller

* controller會檢查目的地為被保護server的tcp封包，若第一個封包的client puzzle通過檢查，
  就新增一條rule，之後同(ip, port) -> (ip, port)的tcp封包就正常移動，不轉送controller檢查
* 由agent告知與server相關的訊息，或是刪除rule等等

### agent.py

* 要使用client puzzle服務的server向agent註冊，會和agent建立tcp連線管理server和client的連線狀態
* server也使用client puzzle向agent溝通
* agent會適度檢查server傳來的訊息合法性

### client.py

* 有很爛的參數介紹，可以指定src, dst的ip, port，可以指定是否要用client puzzle。不用照理說會被block住
* 上述11點exit後可以再對別的server連線

### server.py

* 會向agent發出註冊申請，註冊後成為被client puzzle保護的server
* 可以打指令向agent發送請求:
	1.	open port:X, Y
		X: port number, Y: 可允許最大連線數
	2.	close port:X
	3.	df, src_ip, src_port, dst_port
		向agent刪除該連線，agent檢查合法後會轉送給controller刪除該條rule

### BUG

bug應該很多xD，要做其他功能再加，詳細敘述待補
