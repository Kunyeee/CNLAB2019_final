bastion_config.py 可以生成要產生puzzle需要的prime和generater，預設prime有2048個bit，-k可以調整有幾個bit(要2的倍數)，如果要更換prime和generater的話才要執行，不然只要資料夾裡有bastion_pg.json就能執行下面python檔
generate_server_key.py 可生成server的公鑰私鑰對，對client來說指讀的到公鑰，對server來說他知道私鑰
generate_puzzle.py 可生成puzzle '-l (難度)' 可以控制client puzzle難度到約要解1/2*(2^難度)個puzzle才行，'-c'可以控制產生的channel數，'-s 1'可以讓產生新的puzzle時順便產生puzzle的解，可以方便攻擊者使用(如果必要的話)，預設是關起來的
sever_puzzle.py  提供API函數可提供server載入新puzzle或是驗證當前puzzle等等
client_puzzle.py 提供API函數可提供client載入新puzzle或是解開當前puzzle等等

