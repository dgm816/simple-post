'''simple-post

This is intended to be a very simple python NNTP posting application that can
be fully implemented within a single python file.
'''

import re
import socket
import ssl
import sys

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

def yEncode(char, first=False, last=False):
    '''Encode one character using the yEnc algorithm.
    
    Return the yEnc encoded value and handle the special characters by appending
    the escape character and encoding alternatly. One or two characters will be
    returned each time this function is called.
    
    The 'first' argument has been designed so we encode the characters properly
    if it is the first character of a new line. This will encode period/space/
    tab characters.  Also, passing the 'first' flag inheriently will enable the
    'last' flag (to pick up space/tab characters).
    
    The 'last' argument has been designed to encode the space/tab characters
    properly when the last character of the line is being encoded.
    '''
    
    # check if special rules are being used
    if first == True:
        last = True
    
    # holds our output
    output = ''
    
    # encode the string with yEnc
    e = (ord(char) + 42) % 256
    
    # check for special characters
    if e == 0x00:
        e = (e + 64) % 256
        output = '='
    # the encoded 0x09 (tab char) was removed in version 1.2 of the yenc spec;
    # however, we still should force to encode this character if it is the
    # first or last character of a line
    elif e == 0x09 and last == True:
        e = (e + 64) % 256
        output = '='
    elif e == 0x0a:
        e = (e + 64) % 256
        output = '='
    elif e == 0x0d:
        e = (e + 64) % 256
        output = '='
    # the encoded 0x20 (space char) should be used it it is the first or the
    # last character of a line
    elif e == 0x20 and last == True:
        e = (e + 64) % 256
        output = '='
    # the encoded 0x2e (period) only needs encoding on the first line to adhere
    # to the nntp rfc
    elif e == 0x2e and first == True:
        e = (e + 64) % 256
        output = '='
    elif e == 0x3d:
        e = (e + 64) % 256
        output = '='
    
    # append the encoded value to the output string
    output += chr(e)
    
    # return the value
    return output

def yEncodeData(data, chars=128):
    '''Encode an entire data chunk obeying the formatting rules.
    
    '''
    
    # holds our output
    line = ''
    output = ''
    count = 1
    
    # loop over data passed
    for char in data:
        # encode each character
        if len(line) == 0:
            line += yEncode(char, first=True)
        elif len(line) == chars:
            line += yEncode(char, last=True)
        elif len(data) == count:
            line += yEncode(char, last=True)
        else:
            line += yEncode(char)
        
        # check if we have a full line
        if len(line) >= chars:
            # save to output
            output += line + "\n"
            # clear the line
            line = ''
    
    # check if we have a partial line to append
    if len(line) > 0:
        output += line + "\n"
    
    # return our encoded and formatted data
    return output

if __name__ == '__main__':
    
    header = '''From: develop@winews.net
Newsgroups: yenc
Date: 27 Oct 2001 15:07:44 +0200
Subject: yEnc-Prefix: "testfile.txt" 584 yEnc bytes - yEnc test (1)
Message-ID: <4407f.ra1200@liebchen.winews.net>
Path: liebchen.winews.net!not-for-mail
Lines: 16
X-Newsreader: MyNews

-- 
=ybegin line=128 size=584 name=testfile.txt 
'''

    footer = '''=yend size=584 crc32=ded29f4f
'''
    myFile = file('testfile.txt', 'rb').read()
    
    f = file("output.txt", "wb")
    f.write(header)
    f.write(yEncodeData(myFile))
    f.write(footer)
    
    sys.exit()
    
    # connect to server
    conn = Connect(server, port, use_ssl)
    
    # check for failure
    if conn == None:
        print("Unable to connect to server.")
        sys.exit()
    
    # login to server
    if Login(conn, username, password) == None:
        print("Unable to login to server.")
        conn.close()
        sys.exit()
    
    # quit server connection
    
    # close the connection
    conn.close()