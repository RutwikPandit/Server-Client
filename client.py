import socket               # Import socket module
import os
import pickle
from os.path import expanduser
import random
import signal

def download(filename,address,directory):
	print("1")
	s = socket.socket()         # Create a socket object
	s.connect(address)

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





shared_dir = ""
listen_port = 12347                 # Reserve a port for your service.
while True:
	port = random.randint(8000,60000)
	with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
		if s.connect_ex((socket.gethostname(), port)) != 0:
			listen_port = port
			break
print("listening at:",listen_port)
            



child_pid = os.fork()
if child_pid > 0:
	while True:

		s = socket.socket()         # Create a socket object
		host = socket.gethostname() # Get local machine name
		port_list = [12345,12346]

		print('Enter your choice\n 1: send meta_data\n 2: search\n-1: exit')

		while True:
			try:
				choice = int(input())
				break
			except:
				continue

		valid_choices = {-1,1,2}
		if choice not in  valid_choices:
			continue
		if choice == -1:
			os.kill(child_pid, signal.SIGKILL)
			exit()

		for port in port_list:
			try:
				s.connect((host, port))
			except:
 				print('Could not connect to: ',port)
 				continue

			print('Connected to port:',port)

			s.send((str(choice)).encode());

			if choice == 1:

				print('Input shared directory name:')
				dname = input()
				
				home = expanduser("~")
				shared_dir = home+'/shared_data/' + dname
				file_names = os.listdir(shared_dir)
				
				file_names.append(shared_dir)
				file_names.append(listen_port)
				
				s.send(pickle.dumps(file_names));

			elif choice == 2:

				print("Input filename: ")
				file_name = input()
				s.send(file_name.encode());

				all_choices = s.recv(1024)
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

			
			s.shutdown(socket.SHUT_WR)
			s.close()                  # Close the socket when done
			break
else:
	listen_socket = socket.socket()
	host = socket.gethostname()
	listen_socket.bind((host, listen_port))
	listen_socket.listen(100)
	while True:
		c, addr = listen_socket.accept()
		print("upload request arrived")
		upload(c)


