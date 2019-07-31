from sys import argv
from time import strptime,ctime
from os.path import isfile
from SocketServer import ThreadingTCPServer
from SimpleHTTPServer import SimpleHTTPRequestHandler

if len(argv) !=  2:
    print("Server Port : only one arg expected")
    exit()
else :
    s_port = int(argv[1])


class HTTPCacheRequestHandler(SimpleHTTPRequestHandler):
    def send_head(self):
        if self.command != "POST" and self.headers.get('If-Modified-Since', None) == True:
            fil = self.path.strip("/")
            if isfile(fil):
                z = ctime(getmtime(fil))
                y = self.headers.get('If-Modified-Since',None)
                b = strptime(self.headers.get(y, "%a %b %d %H:%M:%S"))
                a = strptime(z, "%a %b %d %H:%M:%S")
                if b > a:
                    self.send_response(304)
                    self.end_headers()
                    return None
        return SimpleHTTPRequestHandler.send_head(self)

    def end_headers(self):
        self.send_header('Cache-control', 'must-revalidate')
        SimpleHTTPRequestHandler.end_headers(self)

    def do_POST(self):
        self.send_response(200)
        self.send_header('Cache-control', 'no-cache')
        SimpleHTTPRequestHandler.end_headers(self)
host = ""

# try:
Server_url = (host,s_port)
s = ThreadingTCPServer(Server_url, HTTPCacheRequestHandler)
s.allow_reuse_address = 1
s.serve_forever()
# except:
    # pass