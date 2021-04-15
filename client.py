import socket               # Import socket module
import os
import pickle
from os.path import expanduser
import random
import signal
import time

shared_dir = ""

def download(filename,address,directory):
	global shared_dir
	s = socket.socket()         # Create a socket object
	s.connect(address)

	s.send((str(3)).encode())
	time.sleep(1)

	s.send(pickle.dumps((filename,directory)))
	f = open(os.path.join(shared_dir,filename),'wb')
	l = s.recv(1024)
	while (l):
		f.write(l)
		l = s.recv(1024)
	f.close()
	s.shutdown(socket.SHUT_WR)
	print(filename,"downloaded succesfully!")
	s.close()                  # Close the socket when done
	return 0

	

def upload(c):
	tup = c.recv(1024)
	(filename,directory) = pickle.loads(tup)
	print("sending",os.path.join(directory,filename))
	f = open(os.path.join(directory,filename),'rb')
	l = f.read(1024)
	while (l):
		c.send(l)
		l = f.read(1024)
	f.close()
	c.close()
	print("File sent!\nEnter your choice\n 1: send meta_data\n 2: search\n-1: exit")
	return 0





listen_port = 12347                 # Reserve a port for your service.
while True:
	port = random.randint(8000,60000)
	with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
		if s.connect_ex((socket.gethostname(), port)) != 0:
			listen_port = port
			break
print("listening at:",listen_port)
            


def send_metadata(child_socket):
	global shared_dir
	print('Input shared directory name:')
	dname = input()
	
	home = expanduser("~")
	shared_dir = home+'/shared_data/' + dname
	file_names = os.listdir(shared_dir)
	
	file_names.append(shared_dir)
	file_names.append(listen_port)
	
	child_socket.send(pickle.dumps(file_names))


child_pid = os.fork()
if child_pid > 0:

	child_socket = socket.socket()         # Create a socket object
	child_socket.settimeout(5.0)
	host = socket.gethostname() # Get local machine name
	port_list = [12497, 12498, 12499]

	for port in port_list:
		try:
			child_socket.connect((host, port))
			break
		except Exception as ex:
			print('Could not connect to: ', port, " Exception - ",  ex)
			

	print('Connected to port: ', port)

	print('Sharing your Metadata: ')

	#To denote that it is a ON
	child_socket.send((str(5)).encode())
	time.sleep(1)
	#To share metadata with SN
	send_metadata(child_socket)

	while True:

		print('Enter your choice\n 1: send meta_data\n 2: search\n-1: exit')

		while True:
			try:
				choice = int(input())
				break
			except:
				print('Enter a valid choice')
				continue

		valid_choices = {-1,1,2}
		if choice not in  valid_choices:
			continue
		
		child_socket.send((str(choice)).encode());

		if choice == -1:
			os.kill(child_pid, signal.SIGKILL)
			exit()

		if choice == 1:
			send_metadata(child_socket)

		elif choice == 2:

			print("Input filename: ")
			file_name = input()
			child_socket.send(file_name.encode());

			all_choices = child_socket.recv(1024)
			all_choices = pickle.loads(all_choices)
			
			if all_choices == set():
				print("No such file found")
			else:
				print("File found at following locations, press the number to download from it (or press -1 to continue):")
				fileNo = 0
				all_choices = list(all_choices)
				for (location,direc) in all_choices:
					print(fileNo,":",location)
					fileNo+=1
				fileNo = int(input())
				if fileNo!=-1:
					download(file_name,all_choices[fileNo][0],all_choices[fileNo][1])

			
			# child_socket.shutdown(socket.SHUT_WR)
			# child_socket.close()                  # Close the socket when done
			# break
else:
	listen_socket = socket.socket()
	host = socket.gethostname()
	listen_socket.bind((host, listen_port))
	listen_socket.listen(100)
	while True:
		c, addr = listen_socket.accept()
		client_type = int((c.recv(1024)).decode())
		if client_type == 3:
			print("upload request arrived")
			upload(c)


