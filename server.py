import socket               # Import socket module
import pickle
import os

s = socket.socket()         # Create a socket object
host = socket.gethostname() # Get local machine name
port = 12345                # Reserve a port for your service.
s.bind((host, port))        # Bind to the port
s.listen(100)                 # Now wait for client connection.

file_to_addr = {}

while True:
    c, addr = s.accept()     # Establish connection with client.
    print('Got connection from', addr)
    choice = c.recv(1024)
    
    if int(choice.decode()) == 1:

        meta_data = c.recv(1024)
        meta_data = pickle.loads(meta_data)
        print(meta_data)
        addr = list(addr)
        addr[1] = meta_data.pop()
        addr = tuple(addr)
        
        direc = meta_data.pop()
		
        for file_name in meta_data:
            if file_name in file_to_addr:
                file_to_addr[file_name].add((addr,direc))
            else:
                file_to_addr[file_name] = {(addr,direc)} 

        print(file_to_addr)

    elif int(choice.decode()) == 2:

        print('Choice: ',choice.decode())
        fn = c.recv(1024)
        file_name = fn.decode()

        if file_name in file_to_addr:
            all_choices = file_to_addr[file_name]
        else:
            all_choices = set()
        c.send(pickle.dumps(all_choices))

    c.close()                # Close the connection
