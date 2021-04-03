
#include <sys/socket.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <string.h>
#include <stdio.h>
#include <ctype.h>
#include <iostream>
#include <stdlib.h>
#include <string>
#include <fstream>
#define BUFFER_SIZE 1024 //At a single time 1 kb of data will be sent

using namespace std;

int main(int argc, char const *argv[])
{
    char c_message[BUFFER_SIZE];
    string temp;
    string file_name;
	//This is Client socket File descriptor
	int Client_socket_fd = 0;
	int Client_recv;

	unsigned char B_Mem[BUFFER_SIZE] = {0};
	FILE *fp;
	int R_bytes=0;
	long int to_be_received;
	long int network_tbr;
	long int bytesToRead;
	long int bytesRead=0;
	long int readThisTime;
	int dl;
	char overwrite;
	int validity_check=0;

	long int res;
	long int converter_res;
	unsigned char data[BUFFER_SIZE]={0};
	int n_bytes;

	char system_command[16];
	long int bytesSent=0;
	long int bytesToSend;
	long int SentThisTime=0;


	struct sockaddr_in serv_addr;
	int i;
	int port_num = atoi(argv[2]);

	cout<<"Port number client is trying to reach is :"<<port_num<<endl;

	if(port_num<1024 || port_num>65535){
        cout<<"Invalid port number ,please use port number between 1024 and 65535, exiting ...."<<endl;
        return -1;
    }

	//I am using ipv4 TCP with internet protocol.
	Client_socket_fd = socket(AF_INET, SOCK_STREAM, 0);
	if ( Client_socket_fd == -1)
	{
		cout<<"Socket could not be created"<<endl;
		return -2;
	}

    serv_addr.sin_family = AF_INET;     //We need to specify which addresses to listen and talk
	serv_addr.sin_port = htons(port_num);   // Conversion of endian system
    serv_addr.sin_addr.s_addr= INADDR_ANY;



	if (connect(Client_socket_fd, (struct sockaddr *)&serv_addr, sizeof(serv_addr)) < 0)
	{
		cout<<"Cannot connect to server"<<endl;
		return -3;
	}

    bzero(c_message , sizeof(c_message));
    bzero(B_Mem , sizeof(B_Mem));

    while(1){

        bzero(B_Mem , sizeof(B_Mem));
        bzero(c_message , sizeof(c_message));
        R_bytes=0;
        cin.clear();
        cin.sync();
        //cin.ignore();
        cout<<"Please enter the command to the server:";
        cin.getline(c_message,sizeof(c_message));
        cout<<endl;

        if(strcmp(c_message, "LIST" )==0)
        {
            send(Client_socket_fd , c_message , strlen(c_message) , 0 );
            cout<<"Files list received :"<<endl;

            while( 1 )
            {
                read(Client_socket_fd , &network_tbr , sizeof(network_tbr) );
                to_be_received = ntohl(network_tbr);

                if(to_be_received > 0)
                {
                    R_bytes = read(Client_socket_fd, B_Mem , to_be_received );
                    cout<<B_Mem;
                    bzero(B_Mem , sizeof(B_Mem));
                }

                if(to_be_received <= 0){
                    if(to_be_received==0){
                    cout<<endl<<"End of file list"<<endl;
                    break;
                    }

                    if(to_be_received<0){
                    cout<<"Error in reading the file list"<<endl;
                    break;
                    }
                }
            }
            cout<<endl;
            continue;

        }

        if(c_message[0]=='R' && c_message[1]=='E' && c_message[2]=='T' && c_message[3]=='R' && c_message[4]==' ')
        {

            file_name=&c_message[5];
            validity_check=0;
            dl = access(file_name.c_str() , F_OK);
            if(dl==0)
            {
                cout<<"The file"<<file_name<<" already exists in this directory , do you wish to overwrite it ? Enter Y/N:";
                cin>>overwrite;
                cout<<"Entered input is :"<<overwrite<<endl;

                if(overwrite=='Y'){
                    cout<<"File will be downloaded from the server and overwritten"<<endl;
                    validity_check=1;
                }
                else if(overwrite=='N'){
                    cout<<"File in the directory will not be overwritten"<<endl;
                    validity_check=0;
                    continue;
                }
                else{
                    cout<<"Invalid input , file will not be overwritten"<<endl;
                    validity_check=0;
                    continue;
                }

            }

            if(dl==-1){
                cout<<"The file"<<file_name<<" does not exists in this directory , and will be downloaded from the server:"<<endl;
                validity_check=1;
            }

            if(validity_check==0){
                continue;
            }

            send(Client_socket_fd , c_message , strlen(c_message) , 0 );
            //Check whether file exists at server side
            read(Client_socket_fd , B_Mem , 3*sizeof(char));
            cout<<B_Mem<<endl;
            if(B_Mem[0]=='A' && B_Mem[1]=='C' && B_Mem[2]=='K'){
                cout<<"Server has acknowleged the retrival , the file shall now be received."<<endl;
            }
            else{
                cout<<"Server has denied the retrival , the file will not be received."<<endl;
                continue;
            }

            bzero(B_Mem , sizeof(B_Mem));
            network_tbr = 0;
            read(Client_socket_fd , &network_tbr , sizeof(network_tbr) );
            to_be_received = ntohl(network_tbr);

            cout<<"Number of bytes to be received is :"<<to_be_received<<endl;
            bytesToRead = to_be_received;
            bytesRead=0;
            readThisTime=0;

            fp=fopen( &c_message[5] , "wb");
            if(fp==NULL){
                cout<<"Error in creating file.";
                return 1;
            }



            while( bytesToRead > bytesRead )
            {
                if( bytesToRead >= BUFFER_SIZE ){
                    R_bytes = read(Client_socket_fd , B_Mem , BUFFER_SIZE);
                    if(R_bytes<0){
                        cout<<"Read error"<<endl;
                        continue;
                    }
                    bytesRead= bytesRead + R_bytes;
                    cout<<"Bytes received :"<<R_bytes<<endl;
                    cout<<"Bytes read till now :"<<bytesRead<<endl;
                    fwrite(B_Mem , 1 , R_bytes , fp);
                    bzero(B_Mem , sizeof(B_Mem));
                }

                if ( bytesRead < BUFFER_SIZE ){
                    R_bytes = read(Client_socket_fd , B_Mem , bytesToRead - bytesRead);
                    if(R_bytes<0){
                        cout<<"Read error"<<endl;
                        continue;
                    }
                    bytesRead= bytesRead + R_bytes;
                    cout<<"Bytes received :"<<R_bytes<<endl;
                    cout<<"Bytes read till now :"<<bytesRead<<endl;
                    fwrite(B_Mem , 1 , R_bytes , fp);
                    bzero(B_Mem , sizeof(B_Mem));

                }

            }
            cout<<"File downloading complete"<<endl;
            fclose(fp);
            bzero(B_Mem , sizeof(B_Mem));
            bzero(c_message , sizeof(c_message));
            R_bytes=0;
            cin.sync();
            cin.clear();
            continue;
        }

        if(c_message[0]=='Q' && c_message[1]=='U' && c_message[2]=='I' && c_message[3]=='T' ){
            send(Client_socket_fd , c_message , strlen(c_message) , 0 );
            cout<<"This client will now quit"<<endl;
            close(Client_socket_fd);
            return 0;
        }

        if(c_message[0]=='D' && c_message[1]=='E' && c_message[2]=='L' && c_message[3]=='E' && c_message[4]==' ' ){
            send(Client_socket_fd , c_message , strlen(c_message) , 0 );
            cout<<"The Client wishes the server to delete the file:"<<&c_message[5]<<endl;
            read(Client_socket_fd , B_Mem , BUFFER_SIZE);
            cout<<"Server reply:"<<B_Mem<<endl;
            continue;
        }

        if(c_message[0]=='S' && c_message[1]=='T' && c_message[2]=='O' && c_message[3]=='R' && c_message[4]==' ' ){
            //First check if the file to be stored even exists
            file_name=&c_message[5];
            validity_check=0;
            dl = access(file_name.c_str() , F_OK);
            if(dl==0)
            {
                cout<<"The file :"<<file_name<<" exists in this directory"<<endl;;
                validity_check=1;

            }

            if(dl==-1){
                cout<<"The file :"<<file_name<<" does not exists in this directory please make sure the file to be sent in present in the directory."<<endl;
                validity_check=0;
            }

            if(validity_check==0){
                continue;
            }

            //File to be sent does exist then send the command to the server.
            send(Client_socket_fd , c_message , strlen(c_message) , 0 );

            //Check the message from the server whether file will be allowed to be stored
            read(Client_socket_fd , B_Mem , BUFFER_SIZE);
            cout<<B_Mem<<endl;
            if(B_Mem[0]=='A' && B_Mem[1]=='C' && B_Mem[2]=='K'){
                cout<<"Server has acknowleged the storage , the file shall now be sent."<<endl;
            }
            else{
                cout<<"Server has denied the storage , the file will not be sent."<<endl;
                continue;
            }


            fp=fopen( &c_message[5] , "rb");
            if(fp==NULL){
                cout<<"Error in opening file."<<endl;
                continue;
            }
            res=0;
            fseek(fp , 0l , SEEK_END);
            res = ftell(fp);
            fseek(fp , 0l , SEEK_SET);

            cout<<"BUFFER_SIZE of file is bytes:"<<res<<endl;
            converter_res= htonl(res);
            send(Client_socket_fd , &converter_res , sizeof(converter_res) ,0);
            while( 1 )
            {
                bzero(data,sizeof(data));
                n_bytes = fread(data,1,BUFFER_SIZE , fp);
                cout<<"Number of bytes read:"<<n_bytes<<endl;

                if(n_bytes > 0){
                            //cout<<"Sending"<<endl;
                    send(Client_socket_fd , data , (size_t)n_bytes ,0);
                            //cout<<data;
                }

                if (n_bytes<=0){
                    if(feof(fp)){
                            //cout<<"BUFFER_SIZE of data:"<<n_bytes<<endl;
                                //send(i , data , (size_t)n_bytes ,0);
                        cout<<"End of File"<<endl;
                                //continue;
                    }
                    if(ferror(fp)){
                        cout<<"Error Reading"<<endl;
                    }
                    break;
                }
            }
            cout<<"File sent successfully"<<endl;

            continue;
        }

        {
            cout<<"Entered command is not valid"<<endl;

        }


	}

	close(Client_socket_fd);
	return 0;
}
