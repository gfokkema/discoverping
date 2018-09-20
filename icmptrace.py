from datetime import datetime
from queue import Queue
from random import randint
from scapy.layers.inet import ICMP, IP
from scapy.sendrecv import sr1
from threading import Thread
from typing import List

ICMP_STATUS_OK = 0
ICMP_STATUS_TIME_EXCEEDED = 11


def timestampdiff(request: IP, reply: IP) -> float:
    return (datetime.fromtimestamp(reply.time)
            - datetime.fromtimestamp(request.sent_time)).microseconds / 1000


def traceroute(hostname: str, start=1, end=30) -> List:
    pkts = []
    for i in range(start, end):
        request = IP(dst=hostname, id=randint(0, 0xffff), ttl=i) / ICMP()
        reply = sr1(request, retry=3, timeout=2.0, verbose=0)

        if not reply:
            delta = None
            print('{:<30} {:<2} * * *'.format(hostname, i))
        elif reply.payload:
            delta = timestampdiff(request, reply)
            print('{:<30} {:<2} {:<15} {} {}'.format(hostname, i, reply.src, delta, reply.payload.type))
        pkts.append((request, reply, delta))

        if reply and reply.payload and reply.payload.type == ICMP_STATUS_OK:
            return pkts
    return pkts


def loop(input: Queue, output: Queue) -> None:
    while True:
        work = input.get()
        if work:
            pkts = traceroute(work)
            output.put(pkts)
        input.task_done()
        if not work:
            break


def threads(num_threads, input, output):
    tlist = []
    for i in range(0, num_threads):
        t = Thread(target=loop, args=(input, output))
        t.start()
        tlist.append(t)
    return tlist
