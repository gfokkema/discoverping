from datetime import datetime
from networkx.drawing.nx_agraph import graphviz_layout
from random import randint
from scapy.layers.inet import ICMP, IP
from scapy.sendrecv import sr1

import logging
import matplotlib.pyplot as plt
import networkx as nx
import sys

from threadpool import ThreadPool

sys.setrecursionlimit(1500)

ICMP_STATUS_OK = 0
ICMP_STATUS_TIME_EXCEEDED = 11

LOGGER = logging.basicConfig(filename='discoverping.log')


class Hop(object):
    def __init__(self, trace, request, reply):
        self.trace = trace
        self.request = request
        self.reply = reply

    def latency(self):
        if not self.reply:
            return None
        return (datetime.fromtimestamp(self.reply.time)
                - datetime.fromtimestamp(self.request.sent_time)).microseconds / 1000

    def ttl(self):
        return self.request.ttl

    def dst(self):
        return self.trace.dst

    def src(self):
        return self.reply.src if self.reply else None

    def icmp(self):
        return self.reply.payload.type if self.reply else None

    def prev(self):
        for ttl in reversed(range(self.trace.start, self.ttl())):
            prev = self.trace.get(ttl)
            if prev.src():
                return prev
        return None

    def __repr__(self):
        return '{:<30} {:<2} {!r:<15} {} {}'\
            .format(self.dst(), self.ttl(), self.src(), self.latency(), self.icmp())


class TraceRoute(object):
    def __init__(self, dst, start=1, end=30):
        self.start = start
        self.end = end
        self.dst = dst
        self.hops = []
        for ttl in range(start, end):
            if self.ping(ttl) == ICMP_STATUS_OK:
                break

    def get(self, ttl):  # start >= ttl >= end
        return self.hops[ttl - self.start]

    def ping(self, ttl):
        request = IP(dst=self.dst, id=randint(0, 0xffff), ttl=ttl) / ICMP()
        reply = sr1(request, retry=3, timeout=2.0, verbose=0)
        hop = Hop(self, request, reply)
        print(hop)

        self.hops.append(hop)
        return hop.icmp()

    @staticmethod
    def trace(*args, **kwargs):
        return TraceRoute(*args, **kwargs)


class Graph(object):
    def __init__(self, results, graph=nx.DiGraph()):
        self._graph = graph
        for result in results:
            self.process(result)

    def draw(self):
        colors = list(nx.get_edge_attributes(self._graph, 'skip').values())
        pos = graphviz_layout(self._graph, prog='dot')
        options = {
            'edge_cmap': plt.cm.tab10,
            'edge_color': colors,
            'font_size': 8,
            'width': 2,
            'with_labels': True
        }
        nx.draw(self._graph, pos, **options)
        options = {
            'edge_labels': nx.get_edge_attributes(self._graph, 'latency'),
            'font_size': 8,
        }
        nx.draw_networkx_edge_labels(self._graph, pos, **options)

    def process(self, route):
        for hop in route.hops:
            if not hop.src():
                continue

            if hop.src() not in self._graph.nodes:
                self._graph.add_node(hop.src())
            prev = hop.prev()
            if prev and (hop.src(), prev.src()) not in self._graph.edges:
                self._graph.add_edge(hop.src(), prev.src(), skip=(hop.ttl() - prev.ttl()))


def main(hostnames=[], repeat=1):
    pool = ThreadPool(TraceRoute.trace)
    for i in range(0, 1):
        for x in hostnames:
            pool.submit(x)
    pool.join()

    g = Graph(pool)

    g.draw()
    plt.show()


if __name__ == '__main__':
    gntel = ['sip.gntel.nl', 'stun-new.gntel.nl', 'pi02.gntel.nl', 'pi03.gntel.nl', 'mclapi2.gntel.nl',
             'smokeping.gntel.nl', 'cdr1.sig.gntel.nl', 'voip.koekman.nl', 'ips-delft.gntel.nl', 'ips-grun.gntel.nl']
    domains = [*gntel, 'amazon.com', 'aws.amazon.com', 'dumpert.nl', 'google.nl',
               'kpn.nl', 'nl-ix.net', 'nu.nl', 'tweakers.net']
    main(hostnames=domains)
