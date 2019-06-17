if [ $# != 1 ]&&[ $# != 2 ]
then
	echo "Usage: 0/1 [file]"
	echo "0: Run the topo"
	echo "1: Run ryu"
	echo "The default file is final_topo.py or final_ryu.py"
	exit
fi
rm -f *.json *.log
if [ $# == 2 ]
then
	f=$2
else
	if [ $1 == 0 ]
	then
		f="final_topo.py"
	else
		f="./final_ryu.py"
	fi
fi
if [ $1 == "0" ]
then
	sudo -E mn --custom $f --topo=mytopo --mac --switch=ovsk,protocols=OpenFlow13 --controller remote
else
	ryu-manager --verbose $f
fi
