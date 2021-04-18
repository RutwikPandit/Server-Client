import socket               # Import socket module
import os
import pickle
from os.path import expanduser
import random
import signal
import time
import threading
import sys
import datetime


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

                #request= '6:' +str(addr[0])+'-'+str(addr[1])+ ':'+file_name
                #print(request)

                #Search in child and own data
                #Send the request to other SNs
                #SN needs to send the IP:filename:time of the ON.
                self.lock.acquire()
                if file_name in file_to_addr:
                    all_choices = file_to_addr[file_name]
                elif file_name in neighbour_data:
                    all_choices = neighbour_data[file_name]
                else:
                    #request= '6:' +addr+ ':'+file_name
                    print("Could not find the file in either own ONs now neighbour ONs , will send the request to Neighbouring SNs:")
                    print(request)
                    #Cal time
                    #current_time = datetime.datetime.now()
                    #timestamp= current_time.hour
                    #Send request id request=6:ip,port:filename:time to neighbours

                    for port in neighbour_server_ports:
                        print("Request sent to port : ",port)
                        #SN_socket = socket.socket()
                        #SN_socket.connect((host, port))
                        #SN_socket.send((6).encode())
                        #time.sleep(1)
                        #SN_socket.send((6).encode())
                        #SN_socket.close()

                #else:
                        #time.sleep(10)
                    all_choices = set()

                self.lock.release()

                self.child_socket.send(pickle.dumps(all_choices))

            #elif choice[0] == 6:
                #print("Request for content from neighbour , content needed :%s , ip addr of requestor:%s",file_name)

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
        #Download request from unknown ON
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
        #Connection request from other SN
        elif client_type == 4:

            SN_ip = str(self.addr[0]) +':'+ str(self.addr[1])
            print("SN request from : ",SN_ip)
            neighbour_servers.append(SN_ip)
            neighbour_server_ports.append(self.addr[1])
            print("Neighbour servers are: ",neighbour_servers)


            SN_meta_data = self.connecting_socket.recv(1024)
            SN_meta_data = pickle.loads(SN_meta_data)

            add_neighbour_data(SN_meta_data)
            self.lock.acquire()
            neighbour_count += 1

            print("Neighbour count :",neighbour_count)

            self.connecting_socket.send(pickle.dumps(file_to_addr))
            self.lock.release()



        #Connection request from ON
        elif client_type == 5:
            new_thread = threaded_client(self.connecting_socket, self.addr)
            new_thread.start()

        #while true: Keep reading on this port , and if you get a request for 6:ip:file:time , then handle
        #Code for cmd 6
        #If file found , send all_choices to given ip.
        #elif client_type == 6:
            #print("Recieved :",client_type)
            #client_type.split(':')
            #addr=client_type[1]
            #filename=client_type[2]
            #print("Request for content from neighbour , content needed :%s , ip addr of requestor:%s",file_name,addr)



shared_dir = ""

def download(filename,address,directory):
    global shared_dir
    s = socket.socket()
    print("Adress: ",address)
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
    # print("File sent!\nEnter your choice\n 1: send meta_data\n 2: search\n-1: exit")
    return 0





listen_port = int(sys.argv[1])                # Reserve a port for your service.

update_port = int(sys.argv[2])                # Reserve a port for your service.

SN_port = int(sys.argv[3])                # Reserve a port for your service.

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

        print('Enter your choice\n 1: send meta_data\n 2: search\n 3: update to SN \n -1: exit')

        while True:
            try:
                choice = int(input())
                break
            except:
                print('Enter a valid choice')
                continue

        valid_choices = {-1,1,2,3}
        if choice not in  valid_choices:
            continue

        child_socket.send((str(choice)).encode());

        print("Sent choice:",choice)

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

        elif choice == 3:


            child_socket.send((str(update_port)).encode());

            print("Sent port number:",update_port)

            # os.kill(child_pid, signal.SIGKILL)
            # exit()

            while True:

                time.sleep(1)

            print('\n\n\n\n\nOutside sleep \n\n\n\n\n\n')
            
else:

    new_child_pid = os.fork()
    if new_child_pid > 0:
        listen_socket = socket.socket()
        print("Code is here , l port = ",listen_port)
        host = socket.gethostname()
        listen_socket.bind(('0.0.0.0', listen_port))
        listen_socket.listen(5)
        while True:
            print("Code is now here")
            c, addr = listen_socket.accept()
            print("Code is now now here")
            client_type = int((c.recv(1024)).decode())
            if client_type == 3:
                print("upload request arrived")
                upload(c)

    else:

        listen_socket = socket.socket()
        print("Code is here , l port = ",update_port)
        host = socket.gethostname()
        listen_socket.bind(('0.0.0.0', update_port))
        listen_socket.listen(5)
        while True:
            print("Code is now in SN update")
            c, addr = listen_socket.accept()
            print("Code is now now here")
            
            print("SN update request arrived")

            server_socket = socket.socket()         # Create a socket object
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            host = socket.gethostname() # Get local machine name
            port = SN_port               # Reserve a port for your service.
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

            public_servers = [12494, 12495, 12496, 12497, 12498, 12499 ]

            neighbour_servers = []
            neighbour_server_ports = []

            neighbour_info = {}
            neighbour_data = {}
            neighbour_count = 0
            child_count = 0


            if port in public_servers:
                for public_port in public_servers:
                    if public_port > port:
                        try:
                            SN_socket = socket.socket()
                            SN_socket.connect((host, public_port))
                            #To denote that a SN is connecting

                            SN_ip = str(SN_socket.getpeername()[0]) +':'+ str(SN_socket.getpeername()[1])
                            #print(str(SN_ip))
                            neighbour_servers.append(SN_ip)
                            neighbour_server_ports.append(SN_socket.getpeername()[1])
                            print("Neighbour servers are: ",neighbour_servers)

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




