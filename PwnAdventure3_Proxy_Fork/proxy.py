import socket
from threading import Thread

class ProxyToServer(Thread):

  def __init__(self, host, port):
    super(ProxyToServer, self).__init__()
    self.game = None #game client socket not known yet
    self.port = port
    self.host = host
    #Socket example taken from python docs
    self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.server.connect((host, port))

  #run in thread
  def run(self):
    while True:
      data = self.server.recv(4096)
      if data:
        print ("[{}] <- {}".format(self.port, data[:100].hex()))
        # forward to client
        self.game.sendall(data)

class GameToProxy(Thread):

  def __init__(self, host, port):
    super(GameToProxy, self).__init__()
    self.server = None # real server socket not known yet
    self.port = port
    self.host = host
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((host,port))
    sock.listen(1)
    self.game, addr = sock.accept()

  def run(self):
    while True:
      data = self.game.recv(4096)
      if data:
        print ("[{}] -> {}".format(self.port, data[:100].hex()))
        #forward to server
        self.server.sendall(data)

#Master controller of a socket proxy
class Proxy(Thread):
  def __init__(self, from_host, to_host, from_port, to_port):
    super(Proxy, self).__init__()
    self.from_host = from_host
    self.to_host = to_host
    self.from_port = from_port
    self.to_port = to_port

  def run(self):
    while True:
      print("[proxy(from {} - to {}) ] setting up".format(self.from_port, self.to_port))
      self.g2p = GameToProxy(self.from_host, self.from_port)
      print("Listening on {}".format(self.from_port))
      self.p2s = ProxyToServer(self.to_host, self.to_port)
      print("Sending to {}".format(self.to_port))
      print("[proxy(from {} - to {})] connection established".format(self.from_port, self.to_port))
      #give each thread the reference to the other
      self.g2p.server = self.p2s.server
      self.p2s.game = self.g2p.game

      self.g2p.start()
      self.p2s.start()

if __name__ == "__main__":
  master_server = Proxy('0.0.0.0', '127.0.0.1', 3344, 3333)
  master_server.start()
  for port in range(3300,3306):
    game_server = Proxy('0.0.0.0','127.0.0.1',port,port-300)
    game_server.start()
