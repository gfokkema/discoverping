from graph import Graph
from networkx.drawing.nx_agraph import graphviz_layout
from threading import Thread
from queue import Queue
from time import sleep

import icmptrace
import logging
import matplotlib.pyplot as plt
import networkx as nx
import sys

sys.setrecursionlimit(1500)

LOGGER = logging.basicConfig(filename='discoverping.log')


class DiscoverPing:
    def __init__(self, graph=nx.DiGraph()):
        self._graph = graph
        self._threads = []
        self._input = Queue()
        self._output = Queue()

    def join(self):
        for x in range(0, len(self._threads)):
            self._input.put(None)
        self._input.join()
        for t in self._threads:
            t.join()

    def threads(self, num_threads):
        for i in range(0, num_threads):
            t = Thread(target=icmptrace.loop, args=(self._input, self._output))
            self._threads.append(t)
            t.start()

    def run(self, hostnames=[], repeat=1, num_threads=10):
        self.threads(num_threads)
        for i in range(0, repeat):
            for x in hostnames:
                sleep(.5)
                self._input.put(x)
        self.join()

    def process(self):
        while not self._output.empty():
            pkts = self._output.get()
            srcs = [{reply.src: {'latency': latency}} if reply else {None: None}
                    for request, reply, latency in pkts]

            skip = 0
            prev = None
            for cur, attrib in reversed([x for src in srcs for x in src.items()]):
                if not cur and prev:
                    cur = 'pre-{}'.format(prev)
                    attrib = {'latency': None}
                if cur and attrib:
                    if cur not in self._graph.nodes:
                        self._graph.add_node(cur, count=0, **attrib)
                    elif self._graph.nodes[cur]['latency']:
                        self._graph.nodes[cur]['latency'] += attrib['latency']
                    self._graph.nodes[cur]['count'] += 1

                    if prev and not prev == '192.168.5.1' and not prev == '192.168.69.1':
                        if (cur, prev) not in self._graph.edges:
                            self._graph.add_edge(cur, prev, skip=skip)
                        node = self._graph.nodes[prev]
                        edge = self._graph.edges[(cur, prev)]
                        text = ''
                        if node['count'] and node['latency']:
                            text = '{:.1f}'.format(node['latency'] / node['count'])
                        edge['latency'] = text
                    skip = 0
                    prev = cur
                else:
                    skip = skip + 1
        # replies = [reply for request, reply in pkts if reply]
        # TracerouteResult(replies).display()

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
        plt.show()


if __name__ == '__main__':
    gntel = ['sip.gntel.nl', 'stun-new.gntel.nl', 'pi02.gntel.nl', 'pi03.gntel.nl', 'mclapi2.gntel.nl',
               'smokeping.gntel.nl', 'cdr1.sig.gntel.nl', 'voip.koekman.nl', 'ips-delft.gntel.nl', 'ips-grun.gntel.nl'],
    domains = [*gntel, 'amazon.com', 'aws.amazon.com', 'dumpert.nl', 'google.nl',
               'kpn.nl', 'nl-ix.net', 'nu.nl', 'tweakers.net']
    d = DiscoverPing()
    d.run(hostnames=domains, repeat=2, num_threads=5)
    d.process()
    d.draw()
