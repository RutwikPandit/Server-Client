# Server-Client

## Running Code
Create a new folder in the home with name 'shared_data'. Now, create multiple folders in this folder, each representing a folder for a SN or ON.'

Example directory structure
```
home/shared_data
|-S1
|--s1.txt
|-S2
|-S3
|--s3.txt
|-C1
|--c1.txt
```

Initialize the port list in server.py(Line 30) and client.py(Line 83).
Then, on 3 seperate terminals, initiate 3 different SN using this command:
```
python3 server.py <port_no>
```
Run the above command with decreasing port numbers.

After running the command for a server, it will ask for shared directory name. Enter S1/S2/S3 accordingly. Now the SN is ready to accept connections from ONs and other SNs. 

Finally, run the code for ON:
```
python3 client.py
```
Input the shared directory of the ON and select 1 for sharing metadata, 2 for searching and -1 for exit.

Internally, whenever a new connection like SN-SN, SN-ON or ON-ON is made, the first message is a number which denotes the purpose of connection.

-1 - Exit

1 - Sending Metadata

2 - Search

3 - Download request

4 - New SN connection

5 - New ON connection
