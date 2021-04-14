import socket               # Import socket module
import pickle
import os
import threading

server_socket = socket.socket()         # Create a socket object
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
host = socket.gethostname() # Get local machine name
port = 12347                # Reserve a port for your service.
server_socket.bind((host, port))        # Bind to the port
server_socket.listen(100)                 # Now wait for client connection.

file_to_addr = {}

def get_metadata(child_socket, addr, lock):
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

child_list = []



class threaded_client (threading.Thread):
    def __init__(self, child_socket, addr):
        threading.Thread.__init__(self)
        self.child_socket = child_socket
        self.addr = addr
        self.lock = threading.Lock()

    def run(self):
        global file_to_addr
        print("Running thread ", threading.get_ident())
        get_metadata(self.child_socket, self.addr, self.lock)

        while True:

            choice = self.child_socket.recv(1024)
            
            if int(choice.decode()) == 1:

                get_metadata(self.child_socket, self.addr, self.lock)

            elif int(choice.decode()) == 2:

                print('Choice: ',choice.decode())
                fn = self.child_socket.recv(1024)
                file_name = fn.decode()


                if file_name in file_to_addr:
                    self.lock.acquire()
                    all_choices = file_to_addr[file_name]
                    self.lock.release()
                else:
                    all_choices = set()

                self.child_socket.send(pickle.dumps(all_choices))

            elif int(choice.decode()) == -1:
                break

        self.child_socket.close()


thread_count = 0
while True:
    child_socket, addr = server_socket.accept()     # Establish connection with client.
    print('Got connection from', addr)
    new_thread = threaded_client(child_socket, addr)
    new_thread.start()

    thread_count += 1
    print('Thread Count = ', thread_count)

# server_socket.close()