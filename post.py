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

def GetServerResponse(s):
    ''' Get server response.
    
    Get the response to a command send to the NNTP server and return it for use
    by the calling function.
    '''
    
    # receive server response
    data = s.recv(1024)
    
    # parse server response
    code, text = ParseResponse(data)
    
    return code, text

def SendServerCommand(s, command):
    ''' Send a command to the server and get the response.
    
    Send the command out to the server and pass the response back to the calling
    function.
    '''
    
    # send the command to the server
    s.sendall(command)
    
    # get the response from the server
    code, text = GetServerResponse(s)
    
    return code, text

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
    
    # get the servers connection string
    code, text = GetServerResponse(s)
    
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
    
    # send the username to the server
    code, text = SendServerCommand(s, "AUTHINFO USER " + username + "\r\n")
    
    # get code 381 if a password is required
    if code != '381':
        return None
    
    # send the password to the server
    code, text = SendServerCommand(s, "AUTHINFO PASS " + password + "\r\n")
    
    # get code 281 if successfully logged in
    if code != '281':
        return None
    
    # all went well, return true
    return True

def yEncode(char):
    '''Encode one character using the yEnc algorithm.
    
    Return the yEnc encoded value and handle the special characters by appending
    the escape character and encoding alternatly. One or two characters will be
    returned each time this function is called.
    '''
    
    # holds our output
    output = ''
    
    # encode the string with yEnc
    encoded = (ord(char) + 42) % 256
    
    # check for special characters
    if encoded == 0x00:
        encoded = (ord(char) + 64) % 256
        output = '='
    elif encoded == 0x0a:
        encoded = (ord(char) + 64) % 256
        output = '='
    elif encoded == 0x0d:
        encoded = (ord(char) + 64) % 256
        output = '='
    elif encoded == 0x3d:
        encoded = (ord(char) + 64) % 256
        output = '='
    
    # append the encoded value to the output string
    output += chr(encoded)
    
    # return the value
    return output

if __name__ == '__main__':
    
    myFile = file('testfile.txt').read()
    myEncoding = ''
    
    for char in myFile:
        myEncoding += yEncode(char)
    
    quit
    
    # connect to server
    conn = Connect(server, port, use_ssl)
    
    # check for failure
    if conn == None:
        print("Unable to connect to server.")
        quit
    
    # login to server
    if Login(conn, username, password) == None:
        print("Unable to login to server.")
        quit
    
    # quit server connection
    
    # close the connection
    conn.close()