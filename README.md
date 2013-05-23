simple-post
===========

A very simple Python NNTP binary posting application intended to be contained
within one Python file.

This should allow for portability across platforms and serve as an example of
building NNTP related libraries in Python. This project is intended to be very
simple to allow for quick posting to NNTP servers from the command line.
Additional features may be added as time passes to enhance the basic
functionality of the program.

Quick Start
-----------

1. Open up `post.py` and change any of the configuration variables at the top to
   your desired default values.

2. From the command line start simple-post and optionally override any of your
   default values.

3. Sit back, and grab a coffee.

Command Line Options
--------------------

You can access this list at any time using `post.py -h` or `post.py --help` from
the command line. You may need to run it as `python post.py -h` or
`python post.py --help` if your OS cannot find the Python interpreter.

```
usage: post.py [-h] [-v | -q] [-f FROM] [-s SUBJECT] [-n NEWSGROUPS]
               [--host HOST] [--port PORT] [--ssl] [--user USER] [--pass PASS]
               [--chars CHARS] [--size SIZE]
               file [file ...]

post a yEnc binary to a newsgroup group

positional arguments:
  file                  file(s) to post

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose         increase output verbosity
  -q, --quiet           disable output
  -f FROM, --from FROM  from line of the post
  
  -s SUBJECT, --subject SUBJECT
                        subject of the post
						
  -n NEWSGROUPS, --newsgroups NEWSGROUPS
                        newsgroup(s) to post to (comma seperated)
						
  --host HOST           hostname of server
  --port PORT           port for posting server
  --ssl                 use ssl for connecting to server
  --user USER           username for posting server
  --pass PASS           password for posting server
  --chars CHARS         set the max characters per line value
  --size SIZE           set the max size of each part posted
```

Examples
--------

All of these examples assume you are in the same directory as the file you wish
to post.

Post the file 'document.pdf', with the subject 'my favorite document', to the
newsgroup 'alt.binary.test' using the default configuration values stored in
`post.py`:

`post.py -n alt.binary.test -s "my favorite document"  document.pdf`

Post all the .rar files in the current directory:

`post.py -n alt.binary.test -s "here are my rar files"  *.rar`

Post the .txt file, then all the zip files, to two newsgroups:

`post.py -n alt.binary.zips,alt.binaries.full.zips -s "here is my source code"  info.txt *.zip`

Of course you can use any combination to achive your desired effect of the above
command line options.