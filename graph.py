

class Graph:
    def __init__(self, roots=[], nodes={}):
        self._roots = roots
        self._nodes = nodes

    def __repr__(self):
        return '\n'.join([str(x) for x in self._roots])

    def add(self, addrs=[]):
        cur = None
        next_hops = []
        for addr in reversed(addrs):
            if not addr or 'address' not in addr:
                cur = None
                next_hops = []
            else:
                if addr['address'] in self._nodes:
                    self._nodes[addr['address']].add_hops(next_hops)
                else:
                    self._nodes[addr['address']] = Address(**{**addr, 'next_hops': next_hops})

                cur = self._nodes[addr['address']]
                next_hops = [cur]
        if cur and cur not in self._roots:
            self._roots.append(cur)


class Address:
    def __init__(self, address='127.0.0.1', latency=None, next_hops=[]):
        self._address = address
        self._latency = latency
        self._next_hops = set(next_hops)

    def __repr__(self, just=0):
        res = 'Address(\'{}\', {})\n'.format(self._address, self._latency)
        res = res.rjust(just + len(res))
        res += ''.join(['{}'.format(x.__repr__(just=just + 4))
                        for x in self._next_hops if not self.value() == x.value()])
        return res

    def add_hops(self, next_hops):
        self._next_hops.update(next_hops)

    def value(self):
        return self._address


def foo():
    g = Graph()
    g.add([{'address': '1.2.3.4'},
           {'address': '1.2.3.5'},
           {'address': '1.2.3.6'}])
    g.add([{'address': '1.2.3.4'},
           {'address': '2.2.3.5'},
           {'address': '2.2.3.6'}])
    g.add([{'address': '1.2.3.4'},
           {'address': '3.2.3.5'},
           {'address': '3.2.3.6'},
           {'address': '3.2.3.7'}])
    g.add([{'address': '1.2.3.4'},
           {'address': '2.2.3.5'},
           {'address': '3.2.3.6'}])
    g.add([{'address': '1.2.3.4'},
           {'address': '3.2.3.5'},
           {'address': '2.2.3.6'}])
    g.add([{'address': '1.2.3.4'},
           {'address': '3.2.3.6'}])
    print(g)
    print(len(g._nodes))

# a = Address('1.2.3.4', next_hops=[
#     Address('1.2.3.5', next_hops=[Address('1.2.3.6', next_hops=[Address('1.2.3.7', [Address('1.2.3.8')])])]),
#     Address('2.2.3.5', next_hops=[Address('2.2.3.6', next_hops=[Address('2.2.3.7', [Address('2.2.3.8')])])]),
#     Address('3.2.3.5', next_hops=[Address('3.2.3.6', next_hops=[Address('3.2.3.7', [Address('3.2.3.8')])])]),
# ])
