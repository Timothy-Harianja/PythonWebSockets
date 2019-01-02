from socket import socket, AF_INET, SOCK_STREAM
from _thread import *
import hashlib
import codecs

server = ('', 1111)
buffer = (4096)

s = socket(AF_INET, SOCK_STREAM)
try: s.bind(server)
except: print('Error starting the server (binding problem)')

# number of connection requests allowed to be queued
s.listen(5)
clients = []


def send_msg(conn, msg):
    #######################################
    frame = [129]
    frame += [len(msg)]
    frame_to_send = bytearray(frame) + msg
    conn.send(frame_to_send)
    #######################################


def get_key(data):
    try:
        data = data.decode().split('\r\n')
        for line in data:
            if 'Sec-WebSocket-Key' in line:
                return line.split(': ')[1]
    except:
        print('failed to get key')


def generate_accept(key):
    to_hash = key + '258EAFA5-E914-47DA-95CA-C5AB0DC85B11'
    hash = hashlib.sha1(to_hash.encode()).hexdigest()
    return codecs.encode(codecs.decode(hash, 'hex'), 'base64').decode()


def handshake(data, new_connection):
    key = get_key(data)
    accept = generate_accept(key)

    conn.send((
        'HTTP/1.1 101 Switching Protocols\r\n'
        'Upgrade: websocket\r\n'
        'Connection: Upgrade\r\n'
        f'Sec-WebSocket-Accept: {accept}\r\n'
    ).encode())

    new_connection[0] = False
    send_msg(conn, "connected".encode())


def handle_stream(data):
    #######################################
    opcode_and_fin = data[0]
    msg_len = data[1] - 128
    mask = data[2:6]
    encrypted_msg = data[6: 6+msg_len]
    msg = bytearray([encrypted_msg[i] ^ mask[i % 4] for i in range(msg_len)])
    #######################################

    for client in clients:
        send_msg(client, msg)
    print(msg.decode())


def threaded_client(conn):
    clients.append(conn)
    new_connection = [True]  # set as a list to pass by reference
    while True:
        try:
            data = conn.recv(buffer)
            if new_connection[0]:
                handshake(data, new_connection)
            else:
                handle_stream(data)

        except:
            clients.remove(conn)
            break

    conn.close()


while True:
    conn, addr = s.accept()

    print(f'connected to: {addr[0]}:{str(addr[1])}')
    start_new_thread(threaded_client, (conn,))
