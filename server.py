import socket               # Import socket module
import pickle
import os
import threading
from os.path import expanduser
import sys
import time

server_socket = socket.socket()         # Create a socket object
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
host = socket.gethostname() # Get local machine name
port = int(sys.argv[1])                # Reserve a port for your service.
server_socket.bind((host, port))        # Bind to the port
server_socket.listen(100)                 # Now wait for client connection.


print('Input shared directory name:')
dname = input()

home = expanduser("~")
shared_dir = home+'/shared_data/' + dname
file_names = os.listdir(shared_dir)


file_to_addr = {}

for file in file_names:
    file_to_addr[file] = {((host, port),shared_dir)} 

public_servers = [12497, 12498, 12499]


neighbour_data = {}
neighbour_count = 0
child_count = 0


def add_neighbour_data(SN_meta_data):
    global neighbour_data
    lock = threading.Lock()
    lock.acquire()
    for file_name in SN_meta_data:
        if file_name in neighbour_data:
            neighbour_data[file_name].update(SN_meta_data[file_name])
        else:
            neighbour_data[file_name] = SN_meta_data[file_name]

    print("Got neighbour" , neighbour_data)
    lock.release()

if port in public_servers:
    for public_port in public_servers:
        if public_port > port:

            try:
                SN_socket = socket.socket()
                SN_socket.connect((host, public_port))
                #To denote that a SN is connecting 
                num = 4
                SN_socket.send((str(num)).encode())
                time.sleep(1)

                #Send current meta data to other SN
                SN_socket.send(pickle.dumps(file_to_addr))

                #Receive meta data of other SN
                public_neighbour_data = SN_socket.recv(1024)
                public_neighbour_data = pickle.loads(public_neighbour_data)
                print("Received Data back from SN ", public_neighbour_data)
                add_neighbour_data(public_neighbour_data)

            except Exception as ex:
                print("Could not connect to SN: ", ex)


def get_meta_data(child_socket, addr, lock):
    global file_to_addr
    meta_data = child_socket.recv(1024)
    meta_data = pickle.loads(meta_data)
    print(meta_data)
    addr = list(addr)
    addr[1] = meta_data.pop()
    addr = tuple(addr)
    
    direc = meta_data.pop()
    
    lock.acquire()
    for file_name in meta_data:
        if file_name in file_to_addr:
            file_to_addr[file_name].add((addr,direc))
        else:
            file_to_addr[file_name] = {(addr,direc)} 

    print(file_to_addr)
    lock.release()

class threaded_client (threading.Thread):
    def __init__(self, child_socket, addr):
        threading.Thread.__init__(self)
        self.child_socket = child_socket
        self.addr = addr
        self.lock = threading.Lock()

    def run(self):
        global file_to_addr, child_count
        print("Running thread ", threading.get_ident())
        get_meta_data(self.child_socket, self.addr, self.lock)

        self.lock.acquire()
        child_count += 1
        self.lock.release()

        while True:

            choice = int((self.child_socket.recv(1024)).decode())
            
            if choice == 1:

                get_meta_data(self.child_socket, self.addr, self.lock)

            elif choice == 2:

                print('Choice: ',choice)
                fn = self.child_socket.recv(1024)
                file_name = fn.decode()

                #Search in child and own data
                self.lock.acquire()
                if file_name in file_to_addr:
                    all_choices = file_to_addr[file_name]
                elif file_name in neighbour_data:
                    all_choices = neighbour_data[file_name]
                else:
                    all_choices = set()
                
                self.lock.release()

                self.child_socket.send(pickle.dumps(all_choices))

            elif choice == -1:
                break

        self.child_socket.close()



class handle_connection_request (threading.Thread):
    def __init__(self, connecting_socket, addr):
        threading.Thread.__init__(self)
        self.connecting_socket = connecting_socket 
        self.addr = addr
        self.lock = threading.Lock()

    def run(self):
        global neighbour_count

        client_type = int((self.connecting_socket.recv(1024)).decode())
        #Download
        if client_type == 3:
            tup = self.connecting_socket.recv(1024)
            (filename,directory) = pickle.loads(tup)
            print("sending",os.path.join(directory,filename))
            f = open(os.path.join(directory,filename),'rb')
            l = f.read(1024)
            while (l):
                self.connecting_socket.send(l)
                l = f.read(1024)
            f.close()
            self.connecting_socket.close()

        elif client_type == 4:
            SN_ip = str(self.addr[0]) + str(self.addr[1])

            SN_meta_data = self.connecting_socket.recv(1024)
            SN_meta_data = pickle.loads(SN_meta_data)

            
            add_neighbour_data(SN_meta_data)
            self.lock.acquire()
            neighbour_count += 1

            self.connecting_socket.send(pickle.dumps(file_to_addr))
            self.lock.release()

        elif client_type == 5:
            new_thread = threaded_client(self.connecting_socket, self.addr)
            new_thread.start()



thread_count = 0
while True:
    child_socket, addr = server_socket.accept()     # Establish connection with client.
    print('Got connection from', addr)
    #handle request type 
    connection_thread = handle_connection_request(child_socket, addr)
    connection_thread.start()

    thread_count += 1
    print('Thread Count = ', thread_count)









# server_socket.close()