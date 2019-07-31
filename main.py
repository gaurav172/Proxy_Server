import socket
import thread
# import threading
import time
import datetime
import os
# import sys
import json
import base64


cachenumber = 3
logs={}
locks={}
CACHE_DIR = "./cache"
bufsize = 1024
maxcsize = 3
sl="/"

# decide whether to cache or not
# def do_cache_or_not(path):
    

# check whether file is already cached or not
def curcache(path):

    if path.startswith(sl):
        path = path.replace(sl, "", 1)

    clink = CACHE_DIR + sl + path.replace(sl, "*-*")

    if not(os.path.isfile(clink)):
        return clink, None
    else:
        last_mtime = time.strptime(time.ctime(os.path.getmtime(clink)), "%a %b %d %H:%M:%S %Y")
        return clink, last_mtime



def add_log(path, client_addr):


    path = path.replace(sl, "*-*")
    if not path in logs:
        logs[path] = []
    dtime = time.strptime(time.ctime(), "%a %b %d %H:%M:%S %Y")
    logs[path].append({"datetime":dtime,"client":json.dumps(client_addr),})


def get_cache_info(client_addr, info):
    add_log(info["allpath"], client_addr)

    path=info["allpath"]

    try:
        log_arr = logs[path.replace(sl, "*-*")]
        if len(log_arr) < cachenumber : iscache = False
        last_third = log_arr[len(log_arr)-cachenumber]["datetime"]
        delay=datetime.timedelta(minutes=5)
        if delay+datetime.datetime.fromtimestamp(time.mktime(last_third))>=datetime.datetime.now():
            iscache = True
        else:
            iscache = False
    except Exception as e:
        print e
        iscache = False

    clink, last_mtime = curcache(info["allpath"])
    info["iscache"] = iscache
    info["clink"] = clink
    info["last_mtime"] = last_mtime
    return info



# if cache is full then delete the least recently used cache item
def get_space_for_cache(path):
    finc = os.listdir(CACHE_DIR)
    if maxcsize>len(finc):
        return
    file_to_del = [file for file in finc if logs[file][-1]["datetime"] == min(logs[file][-1]["datetime"] 
        for file in finc)][0]


    os.remove(CACHE_DIR+sl+file_to_del)



# insert the header
def insert_if_modified(info):

    # print ("modifying")

    allines = info["client_data"].splitlines()
    while allines[len(allines)-1] == '':
        allines.remove('')

    #header = "If-Modified-Since: " + time.strptime("%a %b %d %H:%M:%S %Y", info["last_mtime"])
    header="If-Modified-Since: "+time.strftime("%a %b %d %H:%M:%S %Y", info["last_mtime"])
    allines.append(header)

    info["client_data"] = "\r\n".join(allines) + "\r\n\r\n"
    return info


def handleGet(client_socket, client_addr, info, bfc):
    try:


        last_mtime = info["last_mtime"]
        clink = info["clink"]
        iscache = info["iscache"]

        socket1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socket1.connect((info["server_url"], info["server_port"]))
        socket1.send(info["client_data"])
        reply = socket1.recv(bufsize)
        adclient=str(client_addr)
        if not(last_mtime):
            if iscache:
                print "Caching %s to %s" % (clink, adclient)


                get_space_for_cache(info["allpath"])
                f = open(clink, "w+")
                # print len(reply), reply
                while True:
                    client_socket.send(reply)
                    f.write(reply)
                    reply = socket1.recv(bufsize)
                    tlen =len(reply)
                    if(not(tlen)):
                        break
                    #print len(reply), reply
                f.close()
                client_socket.send("\r\n\r\n")
            else:
                print "Not caching %s to %s" % (clink, adclient)
                #print len(reply), reply
                while True:
                    client_socket.send(reply)
                    reply = socket1.recv(bufsize)
                    tlen =len(reply)
                    if(not(tlen)):
                        break
                    #print len(reply), reply
                client_socket.send("\r\n\r\n")
        else:
            print "Cache returned from %s to %s" % (clink, adclient)
            # get_access(info["allpath"])


            f = open(clink, 'rb')
            fcdata = f.read(bufsize)
            while True:
                client_socket.send(fcdata)
                fcdata = f.read(bufsize)
                if(not(fcdata)):
                    break
            f.close()
            # leave_access(info["allpath"])

        socket1.close()
        client_socket.close()
        return

    except Exception as e:
        socket1.close()
        client_socket.close()
        print e
        return




def handlePost(client_socket, client_addr, info, bfc):
    try:
        socket1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socket1.connect((info["server_url"], info["server_port"]))
        socket1.send(info["client_data"])
        while True:
            reply = socket1.recv(bufsize)
            if not(len(reply)):
                break
            else:
                client_socket.send(reply)

    except Exception as e:
        print e
        pass

    socket1.close()
    client_socket.close()
    return



def make_proxy_socket():
    proxy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    proxy_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    proxy_socket.bind(("",20100))
    proxy_socket.listen(10)
    print "Serving proxy on %s port %s" % (str(proxy_socket.getsockname()[0]),str(proxy_socket.getsockname()[1]))
    return proxy_socket




def GetBlacklist():
    f = open("blacklist.txt", "rb")
    data = ""
    while True:
        d = f.read()
        if len(d) == 0:
            break
        data = data + d
    f.close()
    blocked = data.split('\n')
    return blocked

def B64_Encode(Admin):
    for i in range(len(Admin)):
        Admin[i]=base64.b64encode(Admin[i])
    return Admin

def getAdmin() :
    f = open("auth.txt","rb")
    Users = ""
    while True:
        u = f.read()
        if len(u) == 0:
            break
        Users =Users + u
    f.close()
    Admin = Users.split('\n')
    return B64_Encode( Admin )


blocked = GetBlacklist()
Admin = getAdmin()

print(Admin)
print(blocked)

def check_block(webserver,port,fl):
    if fl == 1:
        return False
    # print(webserver+":"+port)
    if webserver + ":" + port in blocked:
        return True
    return False

def getser(url,webserver_pos):
    port = -1
    webserver_url = ""
    port_pos = url.find(":")
    if port_pos == -1:
        port = 80
        webserver_url = url[:webserver_pos]
    else:
        port = int(url[port_pos+1:webserver_pos])
        webserver_url = url[:port_pos]
    return webserver_url,port

























proxy_socket = make_proxy_socket()

def handle_one_client(client_conn,client_data,client_addr):

    allines = client_data.split("\n")
    try:
        url = allines[0].split()[1]
    except:
        return
    print("url ",url)
    http_pos = url.find("://")
    if http_pos != -1:
        url = url[(http_pos+3):]
    port_pos = url.find(":")
    webserver_pos = url.find(sl)
    if webserver_pos == -1:
        webserver_pos = len(url)
    webserver = ""
    port = -1


    if port_pos == -1 or webserver_pos < port_pos:
        port = 80
        webserver = url[:webserver_pos]
    else:
        port = int((url[(port_pos+1):])[:webserver_pos-port_pos-1])
        webserver = url[:port_pos]
    print(port)


    flag = [0]
    for line in allines:
        if 'Authorization' in line:
            Z = line.split()
            # print(Z[2])
            if Z[2] in Admin:
                flag[0]=1
    # print(flag[0])
    bl = check_block(webserver,str(port),flag[0])
    print(bl,flag[0])
    if bl:
        client_conn.send("HTTP/1.0 403 FORBIDDEN\r\n")
        client_conn.send("Content-Length: 11\r\n")
        client_conn.send("\r\n")
        client_conn.send("FORBIDDEN\r\n")
        client_conn.send("\r\n\r\n")
        client_conn.close()
        return


    try:
        allines = client_data.splitlines()
        while True:
            if allines[len(allines)-1] == '':
                allines.remove('')
            else:
                break;
        flines = allines[0].split()
        url = flines[1]

        # get starting index of IP
        url_pos = url.find("://")
        if url_pos == -1:
            protocol = "http"
        else:
            protocol = url[:url_pos]
            url = url[(url_pos+3):]

        # get port if any
        # get url path
        port_pos = url.find(":")
        path_pos = url.find(sl)

        if path_pos == -1:
            path_pos = len(url)


        # change request path accordingly
        server_url = url[:port_pos]
        server_port = 80
        if not(port_pos==-1 or path_pos < port_pos):
            server_port = int(url[(port_pos+1):path_pos])
            

        # check for auth
        auth_line = [ line for line in allines if "Authorization" in line]
        if not(len(auth_line)):
            auth_b64 = None
        else:
            auth_b64 = auth_line[0].split()[2]

        # build up request for server
        flines[1] = url[path_pos:]
        allines[0] = ' '.join(flines)
        client_data = "\r\n".join(allines) + '\r\n\r\n'

        info = {
            "allpath" : url,
            "method" : flines[0],
            "protocol" : protocol,
            "server_port" : server_port,
            "server_url" : server_url,
            "client_data" : client_data,
            "auth_b64" : auth_b64,
        }

    except Exception as e:
        print e
        print
        info=None

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
        s.connect((webserver, port))
        s.sendall(client_data)
        while True:
            data = s.recv(1024)
            if len(data) > 0:
                if info["method"] == "GET":
                    info = get_cache_info(client_addr, info)
                    if info["last_mtime"]:
                        info = insert_if_modified(info)
                    handleGet(client_conn, client_addr, info, 0)

                elif info["method"] == "POST":
                    handlePost(client_conn, client_addr, info, 1)
            else:
                break
        s.close()
        client_conn.close()
    except :
        pass


while True:
    (client_conn,clientAddress) = proxy_socket.accept()
    request = client_conn.recv(1024)
    thread.start_new_thread(handle_one_client,(client_conn,request,clientAddress))