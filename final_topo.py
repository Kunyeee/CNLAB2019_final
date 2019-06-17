from mininet.topo import Topo 
class MyTopo (Topo):
	def __init__ (self ):
		Topo.__init__(self )
		h = []
		s = []
		s.append(self.addSwitch('s1'))
		for i in range(1,5):
			h.append(self.addHost('h' + str(i)))
			self.addLink(h[i - 1], s[0])
topos = {'mytopo':(lambda: MyTopo())}
 
