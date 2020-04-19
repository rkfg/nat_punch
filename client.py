'''
Created on 19 Apr 2020

@author: rkfg
'''

import asyncio
import argparse


def addr_from_string(addr):
    result = addr.split(':')
    return (result[0], int(result[1]))

class PunchClientProtocol:
    
    def __init__(self):
        self.wanip = None
        self.sessionid = None
        self.target = None
    
    def connection_made(self, transport):
        self.transport = transport

    async def send_packets(self, number):
        for i in range(number):
            print("Sending packet from %s to %s: %d" % (self.wanip, self.target, i))
            self.transport.sendto(b'\x04packet number %d' % i, self.target)
            await asyncio.sleep(1)

    def datagram_received(self, data, addr):
        if len(data) < 2:
            return
        code = data[0]
        message = data[1:].decode()
        print("Message with code %d received: %s" % (code, message))
        if code == 101:
            print("Pong received from %s" % str(addr))
        if code == 102:
            self.sessionid, self.wanip = message.split(',')
            print("My session id is %s / my IP is %s" % (self.sessionid, self.wanip))
        if code == 103:
            self.target = addr_from_string(message)
            print("Started exchange with client %s" % (self.target,))
            asyncio.get_event_loop().create_task(self.send_packets(10))
        if code == 4:
            print("Data packet received from %s: %s" % (addr, message))

async def main():
    print("Starting UDP client")
    parser = argparse.ArgumentParser(description='UDP NAT punch PoC client')
    parser.add_argument('-p', '--port', type=int, default=37419, help='Port to listen for datagrams at')
    parser.add_argument('-i', '--interval', type=int, default=10, help='Ping interval')
    parser.add_argument('-s', '--session', type=str, help='Ping interval')
    parser.add_argument('address', type=str, help='Pingpong server address')
    args = parser.parse_args()
    addr = addr_from_string(args.address)

    loop = asyncio.get_running_loop()

    transport, _ = await loop.create_datagram_endpoint(
        lambda: PunchClientProtocol(),
        local_addr=('0.0.0.0', args.port))

    try:
        transport.sendto(b'\x02\x00', addr)
        if args.session:
            transport.sendto(b'\x03' + args.session.encode(), addr)
        while True:
            await asyncio.sleep(args.interval)
            transport.sendto(b'\x01\x00', addr)
    finally:
        transport.close()


asyncio.run(main())
