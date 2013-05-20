'''simple-post

This is intended to be a very simple python NNTP posting application that can
be fully implemented within a single python file.
'''

import re
import socket
import ssl

server = 'news.example.com'
port = 119
username = 'username'
password = 'password'
use_ssl = False

def ParseResponse(data):
    '''Parse response from server.
    
    Pass in a single line from the server and it will be broken into its
    component parts (if it is formatted properly). Both the server code as well
    as the string from the response will be returned to the caller.
    
    If the format is not recognized None will be returned.
    '''
    
    # break apart the response code and (optionally) the rest of the line
    match = re.match(r'(\d+)(?: (.*))?\r\n', data)
    if match:
        return match.group(1), match.group(2)
    return None

def Connect(server, port=119, use_ssl=False):
    '''Connect to NNTP server.
    
    Using the server address, port, and a flag to use ssl, we will connect to
    the server and parse the response from the server using standard sockets.
    '''
    
    # create a socket object and connect
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if use_ssl == True:
        s = ssl.wrap_socket(s)
    s.connect((server, port))
    
    # receive server response
    data = s.recv(1024)
    
    # parse server response
    code, text = ParseResponse(data)
    
    # check for success
    if code != '200':
        return None
    else:
        return s

def Login(s, username, password):
    '''Login to server.
    
    Login to the server using a username and password. Check for failure to
    login and intelligently handle server responses.
    '''
    return True

if __name__ == '__main__':
    # connect to server
    conn = Connect(server, port, use_ssl)
    
    # check for failure
    if conn == None:
        print("Unable to connect to server.")
        exit
    
    # login to server
    if Login(conn, username, password) == None:
        print("Unable to login to server.")
        exit
    
    # close the connection
    conn.close()