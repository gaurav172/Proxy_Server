import socket
import threading
import sys
import os

sp = sys.argv[1]

if not (int(sp) <20100 and int(sp)>=20000):
    print("Address outside IIIT cannot be accessed.")
    exit()
Auth = " "
if len(sys.argv) > 2:
    try:
        Auth =" -u "+sys.argv[2]+":"+sys.argv[3]+" "
    except:
        pass
if True:
    os.system("curl --request GET --proxy 127.0.0.1:20100%s127.0.0.1:%s"%(Auth,sp))
    # os.system("curl --request POST --proxy 127.0.0.1:20100%s127.0.0.1:%s"%(Auth,sp))