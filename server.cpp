
#include <unistd.h>
#include <stdio.h>
#include <sys/socket.h>
#include <stdlib.h>
#include <netinet/in.h>
#include <string.h>
#include <string>
#include <ctype.h>
#include <iostream>
#include <fstream>
#include <math.h>
#include <sstream>
#include <arpa/inet.h>
#include <cstring>
#define BUFFER_SIZE 1024



//#define port_num 9000

using namespace std;


int main(int argc, char const *argv[])
{
	char B_Mem[1024] = {0};
	string file_name;
	string temp;
	FILE *fp;
	long int res;
	long int converter_res;
	unsigned char data[BUFFER_SIZE]={0};
	int n_bytes;
	int i;
	char system_command[16];
	long int bytesSent=0;
	long int bytesToSend;
	long int SentThisTime=0;
	int validity_check=0;

	int R_bytes=0;
	long int to_be_received;
	long int network_tbr;
	long int bytesToRead;
	long int bytesRead=0;
	long int readThisTime;

	int dl;
	int bind_error;


	FILE *sc;
	char cmd_line[BUFFER_SIZE];

    int client_socket;
    struct sockaddr_in client_addr[FD_SETSIZE];
    socklen_t c_addr_size[FD_SETSIZE];
	int server_read;

    int server_fd;
    server_fd = socket(AF_INET, SOCK_STREAM, 0);

    struct sockaddr_in server_address;

    int addrlen = sizeof(server_address);
    int port_num = atoi(argv[1]);


    fd_set current_sockets , ready_sockets;
	FD_ZERO(&current_sockets);
	FD_SET(server_fd , &current_sockets);

    cout<<"Port number server is using :"<<port_num<<endl;

    if(port_num<1024 || port_num>65535){
        cout<<"Invalid port number ,please use port number between 1024 and 65535, exiting ...."<<endl;
        return -1;
    }

    server_address.sin_family = AF_INET;
	server_address.sin_addr.s_addr = INADDR_ANY; // Connecting to 0.0.0.0
	server_address.sin_port = htons( port_num ); //Endian conversion

	if ((server_fd) == -1)
	{
		cout<<"Failed to create server socket"<<endl;
		return -2;
	}

    bind_error = bind(server_fd, (struct sockaddr *)&server_address,sizeof(server_address));
    if(bind_error < 0){
        cout<<"Bind error please try again"<<endl;
    }
	listen(server_fd, 10);


	while(1)
	{
        ready_sockets=current_sockets;

        if(select(FD_SETSIZE, &ready_sockets,NULL,NULL,NULL)<0){
            perror("select error");
            exit(EXIT_FAILURE);
        }

        //cout<<"Server is Listening"<<endl;

        for(i=0;i<FD_SETSIZE;i++){
            if(FD_ISSET(i,&ready_sockets)){
                if(i==server_fd){
                    //new connection
                    client_socket = accept(server_fd, (struct sockaddr *)&server_address,(socklen_t*)&addrlen);
                    client_addr[client_socket].sin_addr=server_address.sin_addr;
                    client_addr[client_socket].sin_port=server_address.sin_port;
                    printf("Connection accepted from %s : %d\n", inet_ntoa(client_addr[client_socket].sin_addr),ntohs(client_addr[client_socket].sin_port));
                    FD_SET(client_socket, &current_sockets);
                }
            else
            {
                //read and handle

                bzero(B_Mem , sizeof(B_Mem));
                bzero(cmd_line , sizeof(cmd_line));
                file_name="";
                file_name.clear();
                server_read = read( i , B_Mem, 1024);

                file_name=&B_Mem[5];
                //cout<<file_name<<endl;

                //QUIT IMPLEMENTATION
                if(strcmp(B_Mem , "QUIT")==0){

                        printf("Disconnected from %s : %d\n",inet_ntoa(client_addr[i].sin_addr),ntohs(client_addr[i].sin_port));
                        close(i);
                        FD_CLR(i,&current_sockets);
                        //continue;

                }

                //DELE IMPLEMENTATION
                if(B_Mem[0]=='D' && B_Mem[1]=='E' && B_Mem[2]=='L' && B_Mem[3]=='E' && B_Mem[4]==' ')
                {
                    cout<<"file name received for DELE:"<<file_name.c_str()<<endl;
                    if(file_name == "server.cpp" || file_name == "server.out"){
                        send(i , "Deleting source files is forbidden\n" , sizeof("Deleting source files is forbidden\n") ,0);
                        continue;
                    }



                    dl = access(file_name.c_str() , F_OK);
                    if(dl==0){
                        cout<<"The file :"<<file_name<<" does exist and will be deleted."<<endl;
                        if(remove(file_name.c_str())==0){
                            temp=("The file :"+file_name+" has been deleted.\n");
                            cout<<temp;
                            strcpy(cmd_line , temp.c_str() );
                            send(i , cmd_line , (size_t)strlen(cmd_line) ,0);
                        }
                        else{
                            temp="The file :"+file_name+" could not be deleted.\n";
                            cout<<temp;
                            strcpy(cmd_line , temp.c_str() );
                            send(i , cmd_line , (size_t)strlen(cmd_line) ,0);
                        }
                    }
                    if(dl==-1){
                        temp="The file :"+file_name+" does not exist please check LIST command for files in the directory.\n";
                        cout<<temp;
                        strcpy(cmd_line , temp.c_str() );
                        send(i , cmd_line , (size_t)strlen(cmd_line) ,0);
                    }
                    continue;

                }

                //LIST IMPLEMENTATION
                if(strcmp(B_Mem, "LIST" )==0)
                {
                        sc = popen("ls -l","r");
                        if(sc==NULL){
                            cout<<"Error in listing the files";
                            exit(-1);
                        }
                        while(fgets(cmd_line , sizeof(cmd_line), sc) != NULL){
                            res=0;
                            cout<<"BUFFER_SIZE of buffer :"<<(size_t)strlen(cmd_line)<<endl;
                            res=(size_t)strlen(cmd_line);
                            converter_res= htonl(res);
                            send(i , &converter_res , sizeof(converter_res) ,0);

                            send(i , cmd_line , (size_t)strlen(cmd_line) ,0);
                        }
                        res=(size_t)0;
                        converter_res= htonl(res);
                        send(i , &converter_res , sizeof(converter_res) ,0);

                        pclose(sc);

                        cout<<"List of files sent successfully"<<endl;
                        continue;
                }

                //RETR IMPLEMENTATION
                if(B_Mem[0]=='R' && B_Mem[1]=='E' && B_Mem[2]=='T' && B_Mem[3]=='R' && B_Mem[4]==' ')
                {
                    cout<<"file name received for RETR:"<<file_name.c_str()<<endl;
                    //first check if the file to be returned even exists.
                    dl = access(file_name.c_str() , F_OK);
                    if(dl==0){
                        cout<<"The file :"<<file_name<<" does exist and will be sent to client."<<endl;
                        temp="ACK";
                        strcpy(cmd_line , "ACK" );
                        send(i , cmd_line , (size_t)strlen(cmd_line) ,0);
                        //send ack to client
                    }
                    if(dl==-1){
                        temp="DEN";
                        cout<<temp<<endl;
                        strcpy(cmd_line , "DEN" );
                        send(i , cmd_line , (size_t)strlen(cmd_line) ,0);
                        //doesnt exist or cant be accessed , due to some protection then send denial to the client.
                        continue;
                    }
                    //if it can be sent then start the sending procedure
                    fp=fopen( file_name.c_str() , "rb");
                    if(fp==NULL)
                    {
                        perror("Error in reading file");
                        close(i);
                        FD_CLR(i,&current_sockets);
                        exit(1);
                    }
                    res=0;
                    fseek(fp , 0l , SEEK_END);
                    res = ftell(fp);
                    fseek(fp , 0l , SEEK_SET);
                    //send the size of the file to be sent to the client , max of 4gb can transferred.
                    cout<<"Size of file is bytes:"<<res<<endl;
                    converter_res= htonl(res);
                    send(i , &converter_res , sizeof(converter_res) ,0);

                    while( 1 ) //send data in 1 kb chunks
                    {
                        bzero(data,sizeof(data));
                        n_bytes = fread(data,1,BUFFER_SIZE , fp);
                        cout<<"Number of bytes read:"<<n_bytes<<endl;

                        if(n_bytes > 0){
                            send(i , data , (size_t)n_bytes ,0);

                        }

                        if (n_bytes<=0){
                            if(feof(fp)){
                                cout<<"End of File"<<endl;
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

                //STOR IMPLEMENTATION
                if(B_Mem[0]=='S' && B_Mem[1]=='T' && B_Mem[2]=='O' && B_Mem[3]=='R' && B_Mem[4]==' ')
                {

                    file_name=&B_Mem[5];
                    validity_check=0;
                    dl = access(file_name.c_str() , F_OK);
                    if(dl==0)
                    {
                        cout<<"The file :"<<file_name<<" already exists in this directory"<<endl;;
                        //send the client a message that file cannot be stored
                        temp="DEN";
                        strcpy(cmd_line , temp.c_str() );
                        send(i , cmd_line , (size_t)strlen(cmd_line) ,0);
                        continue;
                    }

                    if(dl==-1){
                        cout<<"The file :"<<file_name<<" does not exists in this directory , and will be downloaded from the client:"<<endl;
                        validity_check=1;
                        //send the client a message that file will be allowed to store and let him send the file now.
                        temp="ACK";
                        strcpy(cmd_line , temp.c_str() );
                        send(i , cmd_line , (size_t)strlen(cmd_line) ,0);
                    }

                    if(validity_check==0){
                        continue;
                    }
                    //The stroage is valid , start the file reception
                    fp=fopen( &B_Mem[5] , "wb");
                    if(fp==NULL){
                        cout<<"Error in creating file.";
                    return 1;
                    }

                    read(i , &network_tbr , sizeof(network_tbr) );
                    to_be_received = ntohl(network_tbr);
                    //Read from the client about how many bytes to be received , max of 4gb can transferred.
                    cout<<"Number of bytes to be received is :"<<to_be_received<<endl;
                    bytesToRead = to_be_received;
                    bytesRead=0;
                    readThisTime=0;
                    while( bytesToRead > bytesRead )
                    {
                        if( bytesToRead >= BUFFER_SIZE ){
                            R_bytes = read(i , cmd_line , BUFFER_SIZE);
                            if(R_bytes<0){
                                cout<<"Read error"<<endl;
                                continue;
                            }
                            bytesRead= bytesRead + R_bytes;
                            cout<<"Bytes received :"<<R_bytes<<endl;
                            cout<<"Bytes read till now :"<<bytesRead<<endl;
                            fwrite(cmd_line , 1 , R_bytes , fp);
                            bzero(cmd_line , sizeof(cmd_line));

                        }

                        if ( bytesRead < BUFFER_SIZE )
                        {
                            R_bytes = read(i , cmd_line , bytesToRead - bytesRead);
                            if(R_bytes<0){
                                cout<<"Read error"<<endl;
                                continue;
                            }
                            bytesRead= bytesRead + R_bytes;
                            cout<<"Bytes received :"<<R_bytes<<endl;
                            cout<<"Bytes read till now :"<<bytesRead<<endl;
                            fwrite(cmd_line , 1 , R_bytes , fp);
                            bzero(cmd_line , sizeof(B_Mem));

                        }

                    }

                cout<<"File downloading complete"<<endl;
                fclose(fp);
                bzero(B_Mem , sizeof(B_Mem));
                bzero(cmd_line , sizeof(cmd_line));
                R_bytes=0;
                continue;
            }




            }//end of read and handle

        }
    }


    }


    close(client_socket);

	return 0;
}
