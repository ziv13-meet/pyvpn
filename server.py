import os
import fcntl
import struct
import socket

from subprocess import check_call
from typing import Tuple, Callable, Dict, Optional
from contextlib import contextmanager, ExitStack
from select import poll, POLLOUT

import click

from cli_utils import iface_type, endpoint_type


TUNSETIFF = 0x400454ca
TUNSETOWNER = TUNSETIFF + 2

IFF_TUN = 0x0001
IFF_TAP = 0x0002
IFF_NO_PI = 0x1000


class TunEndpoint:
    def __init__(self, iface_name: str, ):
        self.iface_name = iface_name

        print(f"Created tunnel device '{iface_name}'")
        self.fd = os.open("/dev/net/tun", os.O_RDWR)

        ifr = struct.pack('16sH', iface_name.encode(), IFF_TUN | IFF_NO_PI)
        fcntl.ioctl(self.fd, TUNSETIFF, ifr)
        fcntl.ioctl(self.fd, TUNSETOWNER, 1000)

        fcntl.fcntl(self.fd, fcntl.F_SETFL, os.O_NONBLOCK)

    def link_up(self):
        print("Set interface link up")
        check_call(f"ip link set dev {self.iface_name} up".split())

    def close(self) -> None:
        os.close(self.fd)

    def read(self) -> Optional[str]:
        return os.read(self.fd, 4096)

    def write(self, data) -> None:
        return os.write(self.fd, data)

    def fileno(self) -> int:
        return self.fd


@contextmanager
def create_tunnel(iface_name: str) -> TunEndpoint:
    tun_dev = TunEndpoint(iface_name)
    try:
        tun_dev.link_up()
        yield tun_dev
    finally:
        tun_dev.close()


F = Tuple[socket.socket, Tuple[str, int]]


@contextmanager
def udp_socket(host: str, port: int) -> F:
    print("Creating UDP socket")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.bind(("0.0.0.0", port))
        sock.setblocking(False)
        yield sock, (host, port)
    finally:
        sock.close()


def vpn_poll(udp_sock: F, tun: TunEndpoint):
    sock, remote = udp_sock

    def tun2sock() -> None:
        try:
            data = tun.read()
            sock.sendto(data, remote)
        except BlockingIOError: pass

    def sock2tun() -> None:
        try:
            data = sock.recv(16536)
            tun.write(data)
        except BlockingIOError: pass

    poll_obj = poll()

    print("Registering tunnel FD in polling object")
    poll_obj.register(sock.fileno(), POLLOUT)
    poll_obj.register(tun.fileno(), POLLOUT)

    fd2cb = {
        sock.fileno(): sock2tun,
        tun.fileno(): tun2sock,
    }

    return lambda: [fd2cb[fd]() for (fd, event) in poll_obj.poll()]


@click.command()
@click.option("--iface", required=True, type=iface_type, help="TUN/TAP interface name")
@click.option("--endpoint", required=True, type=endpoint_type, help="Remote endpoint to connect")
def cli(iface: str, endpoint: Tuple[str, int]):
    with ExitStack() as stack:
        vpn_poll_cb = vpn_poll(stack.enter_context(udp_socket(*endpoint)),
                               stack.enter_context(create_tunnel(iface)))

        print("Polling tunnel forever...")
        while True:
            vpn_poll_cb()

        print("Terminating ...")


import asyncio


async def func(a):
    print(1)
    await asyncio.sleep(a)
    print(2)

async def main():
    print(8)
    await asyncio.gather(func(3), func(1), func(4))
    print(9)


if __name__ == "__main__":
    # cli()
    asyncio.run(main())
