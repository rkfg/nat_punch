'''
Created on 19 Apr 2020

@author: rkfg
'''

import asyncio
from random import randint
import argparse


''' opcodes:
 1 - ping
 101 - pong
 2 - get my WAN address and session id
 102 - returned WAN address and session id
 3 - connect to another session id
 103 - returned IP corresponding to that session id
 4 - data packet
'''


class PunchServerProtocol:

    def __init__(self):
        self.sessions = {}
        self.sessionids = {}

    def connection_made(self, transport):
        self.transport = transport

    def addr_to_str(self, addr):
        return "%s:%d" % addr

    def datagram_received(self, data, addr):
        if len(data) < 2:
            return
        if addr not in self.sessions:
            sessid = randint(0, 1e9)
            self.sessions[addr] = sessid
            self.sessionids[sessid] = addr
            print("New session for %s started: %d" % (addr, sessid))
        code = data[0]
        message = data[1:].decode()
        print("Message with code %d received: %s" % (code, message))
        if code == 1:
            self.transport.sendto(b'\x65\x00', addr)
        if code == 2:
            self.transport.sendto(("\x66%d,%s" % (self.sessions[addr],
                                  self.addr_to_str(addr))).encode(), addr)
        if code == 3:
            try:
                targetid = int(message)
                if targetid not in self.sessionids:
                    print("Unknown session %d" % targetid)
                    return
                targetaddr = self.sessionids[targetid]
                self.transport.sendto(b'\x67' + self.addr_to_str(addr)
                                      .encode(), targetaddr)
                self.transport.sendto(b'\x67' + self.addr_to_str(targetaddr)
                                      .encode(), addr)
            except Exception:
                print("Incorrect session id %s" % message)


async def main():
    print("Starting UDP server")
    parser = argparse.ArgumentParser(description='UDP NAT punch PoC server')
    parser.add_argument('-p', '--port', type=int, default=37419, help='Port to listen for datagrams at')
    args = parser.parse_args()

    loop = asyncio.get_event_loop()

    transport, _ = await loop.create_datagram_endpoint(
        lambda: PunchServerProtocol(),
        local_addr=('0.0.0.0', args.port))

    try:
        while True:
            await asyncio.sleep(1)
    finally:
        transport.close()


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
