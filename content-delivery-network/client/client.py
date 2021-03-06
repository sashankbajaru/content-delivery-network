import socket                   # Import socket module
import pickle
import os
import threading
import time 
import json

ORIGIN_PORT = 50033

def receiveFile (s, addr):
  host = addr[0]
  if(s.recv(1024) != "000"):
  	return
  s.send ('1')
  file_size = s.recv(1024)
  print(file_size)
  (filename, size) = file_size.split ('||||')
  size = int(size)
  print ("File size =", size)
  s.send ('11')
  full_path = os.path.join (filename)
  fname = full_path.split('/')[-1]
  dir_path = '/'.join(full_path.split('/')[:-1])
  os.system("mkdir -p " + dir_path)

  with open(full_path, 'wb') as f:
    print ('file opened')
    chunks = size / 1024
    last_size = size - chunks * 1024
    print ('(chunks, last_size) -> (%d, %d)' %(chunks, last_size))
    received = 0
    while received < size:
      data = s.recv (size - received)
      f.write (data)
      received += len (data)
  print ('file closed:', full_path)
  s.send ('111')


def connectOrigin(host):
	s = socket.socket()
	# host = "localhost"
	# host = socket.gethostbyname("127.0.0.1")
	
	if host == "localhost" or host == "127.0.0.1":
		host = socket.gethostname()
	s.connect((host, ORIGIN_PORT))
	s.send("a/get-pip.py")
	LB = s.recv(1024)
	s.close()
	return LB

def connectLB(LB):
	LB_ip = LB.split('_')[0]
	if LB_ip == "localhost" or LB_ip == "127.0.0.1":
		LB_ip = socket.gethostname()
	LB_port = int(LB.split('_')[1])
	print (LB_ip, LB_port)
	s = socket.socket()
	with open('config.json', 'r') as f:
		ip_self = json.load(f)['ip_self']
	if(ip_self == LB_ip):
		LB_ip = socket.gethostname()
	s.connect((LB_ip, LB_port))
	s.send("Allot me a replica")
	replica = s.recv(1024)
	s.close()
	print('replica is: ',replica)
	return replica


def connectReplica(replica, fname):

	replica_ip = replica.split('_')[0]
	replica_port = int(replica.split('_')[1])
	print (replica_ip, replica_port)
	s = socket.socket()

	with open('config.json', 'r') as f:
		ip_self = json.load(f)['ip_self']
	if(ip_self == replica_ip):
		replica_ip = socket.gethostname()

	s.connect((replica_ip, replica_port))
	strng = s.recv(1024)
	print("Message from the replica server : ", strng)
	if(strng == "Welcome to the world of CDN"):
		s.send("Give me this file")
		if(s.recv(1024) != "Ready"):
			s.close()
			return
		s.send(fname)
		msg = s.recv(1024)
		print(msg)
		if(msg == "File Found"):
			receiveFile (s, replica_ip)
		else:
			print("Error 404 File Not Found")

		s.close()
	
	
def main():
	url_ttl = 30
	url_cache_time = None
	replica = None
	while True:
		fname = raw_input("Enter filename to fetch")
		origin_ip = 'localhost'
		if url_cache_time is None or time.time() - url_cache_time > url_ttl:
			LB = connectOrigin(origin_ip)
			replica  = connectLB(LB)
			print('LB is: ',LB)
			url_cache_time = time.time()
		connectReplica(replica, fname)

if __name__ == "__main__":
	main()
