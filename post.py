"""simple-post

This is intended to be a very simple python NNTP posting application that can
be fully implemented within a single python file.
"""

import argparse
import glob
import os
import re
import socket
import ssl
import sys
import zlib

# Begin configuration area

server = 'news.example.com'
port = 119
username = 'username'
password = 'password'
use_ssl = False

fromAddress = "Anonymous User <anonymous@example.com>"
subject = "This Is Only A Test"
newsgroups = "test"

# with around 3% increase in size for encoding this should leave us with around
# 2012 lines or so.
# figure your own values with:   (defaultPartSize * 1.03) / defaultCharsPerLine
defaultCharsPerLine = 256
defaultPartSize = 500000

# general layout of subject lines
#   {s} - subject passed
#   {f} - file name
#   {b} - bytes (size of file)
#   {c} - current part
#   {t} - total parts
subject_single_template = '[{s}] "{f}" yEnc {b} bytes'
subject_multi_template = '[{s}] "{f}" yEnc ({c}/{t}) {b} bytes'

# End configuration area


def ParseResponse(data):
    """Parse response from server.

    Pass in a single line from the server and it will be broken into its
    component parts (if it is formatted properly). Both the server code as well
    as the string from the response will be returned to the caller.

    If the format is not recognized None will be returned.
    """
    
    # break apart the response code and (optionally) the rest of the line
    match = re.match(r'(\d+)(?: (.*))?\r\n', data)
    if match:
        return match.group(1), match.group(2)
    return None


def GetServerResponse(s):
    """ Get server response.

    Get the response to a command send to the NNTP server and return it for use
    by the calling function.
    """
    
    # receive server response
    data = s.recv(1024)
    
    # parse server response
    code, text = ParseResponse(data)
    
    return code, text


def SendServerCommand(s, command):
    """ Send a command to the server and get the response.

    Send the command out to the server and pass the response back to the calling
    function.
    """
    
    # send the command to the server
    s.sendall(command)
    
    # get the response from the server
    code, text = GetServerResponse(s)
    
    return code, text


def Connect(server, port=119, use_ssl=False):
    """Connect to NNTP server.

    Using the server address, port, and a flag to use ssl, we will connect to
    the server and parse the response from the server using standard sockets.
    """
    
    # create a socket object and connect
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if use_ssl:
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
    """Login to server.

    Login to the server using a username and password. Check for failure to
    login and intelligently handle server responses.
    """
    
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


def Post(s, fromHeader, subjectHeader, newsgroupsHeader, article, filename):
    """Post a binary article to a newsgroup.

    """
    
    # send the post command to the server
    code, text = SendServerCommand(s, "POST\r\n")
    
    # get code 340 if we're ok to post
    if code != '340':
        return None
    
    s.sendall("From: " + fromHeader + "\r\n")
    s.sendall("Subject: " + subjectHeader + "\r\n")
    s.sendall("Newsgroups: " + newsgroupsHeader + "\r\n")
    s.sendall("\r\n")
    s.sendall(article)
    
    # send our end of transmission character
    code, text = SendServerCommand(s, ".\r\n")
    
    # get code 240 if the server accepted our post
    if code != '240':
        return None
    
    return True


def yEncode(char, first=False, last=False):
    """Encode one character using the yEnc algorithm.

    Return the yEnc encoded value and handle the special characters by appending
    the escape character and encoding alternately. One or two characters will be
    returned each time this function is called.

    The 'first' argument has been designed so we encode the characters properly
    if it is the first character of a new line. This will encode period/space/
    tab characters.  Also, passing the 'first' flag inherently will enable the
    'last' flag (to pick up space/tab characters).

    The 'last' argument has been designed to encode the space/tab characters
    properly when the last character of the line is being encoded.
    """
    
    # check if special rules are being used
    if first:
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


def yEncodeData(data, chars):
    """Encode an entire data chunk obeying the formatting rules.

    Using the yEncode function to do the actual work of encoding, yEncodeData
    will pass along things like first/last character flags which will cause
    yEncode to use alternate encoding (encode spaces/tabs at the begining/end
    and encode periods at the start of a line).
    """
    
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
            output += line + "\r\n"
            # clear the line
            line = ''
    
    # check if we have a partial line to append
    if len(line) > 0:
        output += line + "\r\n"
    
    # return our encoded and formatted data
    return output


def yEncodeSingle(filename, chars):
    """Encode a single (non-multipart) yEnc message.

    Useing yEncodeData we will encode the data passed to us into a yEnc message
    with header/footer attached.

    This function does not support multi-part yEnc messages.
    """

    # holds our output
    output = ''
    
    # get the size of the file.
    size = os.path.getsize(filename)
    
    # read in the file
    data = file(filename, 'rb').read()
    
    # store crc of data before encoding
    crc = zlib.crc32(data)
    
    # attach the header
    output = '=ybegin line=' + str(chars) + ' size=' + str(size) + ' name=' + filename + '\r\n'
    
    # append yEnc data
    output += yEncodeData(data, chars)
    
    # attach the footer
    output += '=yend size=' + str(size) + ' crc32=' + "%08x"%(crc & 0xFFFFFFFF) + '\r\n'
    
    # return our encoded and formatted data
    return output


def yEncodeMultiple(filename, partSize, chars):
    """Encode a multipart yEnc message.

    Useing yEncodeData we will encode the data passed to us into a number of
    yEnc messages with headers/footers attached.

    This function only supports multi-part yEnc messages.
    """
    
    # holds our output
    output = []
    
    # get the size of the file.
    size = os.path.getsize(filename)
    
    # read in the file
    data = file(filename, 'rb').read()
    
    # determine number of parts
    totalParts = size / partSize
    if (size % partSize) != 0:
        totalParts += 1
    
    # store crc of data before encoding
    crc = zlib.crc32(data)
    
    # loop for each part
    for i in range(totalParts):
        
        # determine our start/stop offsets
        startOffset = i * partSize
        stopOffset = (i+1) * partSize
        if stopOffset > size:
            stopOffset = size
        
        # grab the portion of the data for this part
        partData = data[startOffset:stopOffset]
        
        # determine the part size
        partSize = len(partData)
        
        # store crc of this parts data before encoding
        pcrc = zlib.crc32(partData)
        
        # attach the header
        partOutput = '=ybegin part=' + str(i+1) + ' line=' + str(chars) + ' size=' + str(size) + ' name=' + filename + '\r\n'
        
        # attach the part header
        partOutput += '=ypart begin=' + str(startOffset+1) + ' end=' + str(stopOffset) + '\r\n'
        
        # append yEnc data
        partOutput += yEncodeData(partData, chars)
        
        # attach the footer
        # part=10 pcrc32=12a45c78
        partOutput += '=yend size=' + str(partSize) + ' part=' + str(i+1) + ' pcrc=' + "%08x"%(pcrc & 0xFFFFFFFF) + ' crc32=' + "%08x"%(crc & 0xFFFFFFFF) + '\r\n'
        
        # append to our output list
        output.append(partOutput)
    
    # return our encoded and formatted data
    return output


if __name__ == '__main__':
    
    # argument parsing comes first
    parser = argparse.ArgumentParser(description="post a yEnc binary to a newsgroup group")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-v", "--verbose", help="increase output verbosity", action="store_true")
    group.add_argument("-q", "--quiet", help="disable output", action="store_true")
    parser.add_argument("file", help="file(s) to post", nargs="+")
    parser.add_argument("-f", "--from", help="from line of the post")
    parser.add_argument("-s", "--subject", help="subject of the post")
    parser.add_argument("-n", "--newsgroups", help="newsgroup(s) to post to (comma seperated)")
    parser.add_argument("--host", help="hostname of server")
    parser.add_argument("--port", help="port for posting server", type=int)
    parser.add_argument("--ssl", help="use ssl for connecting to server", action="store_true")
    parser.add_argument("--user", help="username for posting server")
    parser.add_argument("--pass", help="password for posting server")
    parser.add_argument("--chars", help="set the max characters per line value")
    parser.add_argument("--size", help="set the max size of each part posted")
    args = parser.parse_args()
    
    # override any passed values
    if getattr(args, 'from'):
        fromAddress = getattr(args, 'from')
    if args.subject:
        subject = args.subject
    if args.newsgroups:
        newsgroups = args.newsgroups
    if args.host:
        server = args.host
    if args.port:
        port = args.port
    if args.ssl:
        use_ssl = True
    if args.user:
        username = args.user
    if getattr(args, 'pass'):
        password = getattr(args, 'pass')
    if args.chars:
        defaultCharsPerLine = args.chars
    if args.size:
        defaultPartSize = args.size
    
    # holds our files
    files = []
    
    # expand any patterns pass as files
    for pattern in args.file:
        files += glob.glob(pattern)
    
    # connect to server
    conn = Connect(server, port, use_ssl)
    
    # check for failure
    if conn is None:
        print("Unable to connect to server.")
        sys.exit()
    
    # login to server
    if Login(conn, username, password) is None:
        print("Unable to login to server.")
        conn.close()
        sys.exit()
    
    # loop over all the input files
    for filename in files:
        
        # determine if we should post this multipart
        size = os.path.getsize(filename)
        
        # sigle or multipart?
        if size <= defaultPartSize:
            
            # build single part
            article = yEncodeSingle(filename, defaultCharsPerLine)
            
            # build subject
            mySubject = subject_single_template
            mySubject = mySubject.replace('{s}', subject)
            mySubject = mySubject.replace('{f}', filename)
            mySubject = mySubject.replace('{b}', str(size))
            
            # post single part
            if Post(conn, fromAddress, mySubject, newsgroups, article, filename) is None:
                print("Unable to post to server.")
                conn.close()
                sys.exit()
        
        else:
            
            # build multipart
            data = yEncodeMultiple(filename, defaultPartSize, defaultCharsPerLine)
            currentPart = 1
            totalParts = len(data)
            
            for article in data:
                # build a subject for this part
                mySubject = subject_multi_template
                mySubject = mySubject.replace('{s}', subject)
                mySubject = mySubject.replace('{f}', filename)
                mySubject = mySubject.replace('{c}', str(currentPart))
                mySubject = mySubject.replace('{t}', str(totalParts))
                mySubject = mySubject.replace('{b}', str(size))
                
                # post a part
                if Post(conn, fromAddress, mySubject, newsgroups, article, filename) is None:
                    print("Unable to post to server.")
                    conn.close()
                    sys.exit()
                    
                # update for our next part
                currentPart += 1
    
    # close the connection
    conn.close()