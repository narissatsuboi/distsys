"""
Bellman-Ford Implementation
:authors: Narissa Tsuboi
:version: 1
"""
from math import log

# commonly used dict keys
TIMESTAMP, CROSS, PRICE = 'timestamp', 'cross', 'price'


class BellmanFord(object):

    def __init__(self, graph):
        """ Inits a new instance of the Bellman Ford algorithm on data passed in thru
        the object constructor.
        """
        # holds vertex lists representing analysis space
        self.graph = graph

        # holds the current number of distinct vertices
        self.num_vertices = len(graph)

    def add_edge(self, start_vertex, end_vertex, edge_dist):
        """

        """
        # take the negative log of the exchange rate per BF algorithm
        edge_dist = -1 * log(edge_dist)

        # add new data point to graph
        self.graph.append([start_vertex, end_vertex, edge_dist])

    def printArr(self, dist):
        print('Vertex Distance from Source')
        for i in range(self.num_vertices):
            print('{}\t\t{}'.format(i, dist[i]))

    def shortest_paths(self, start_vertex, tolerance=0):
        """
        Finds the shortest paths (sum of edge weights) from start_vertex to every other
        vertex.
        Detects if there are negative cycles and reports the first cycle it finds.
        Edges may be negative.

        For relaxation and cycle detection, use tolerance. Only relaxations resulting in an
        improvement greater than tolerance are considered.

        For negative cycle detection, if the sum of the weights is greater than (
        -tolerance) it is not reported as a negative cycle. This is useful when circuits
        are expected to be close to zero.

        :param start_vertex: start of all paths
        :param tolerance: only if a path is more than tolerance will it be relaxed
        :return: distance, predecessor, negative cycle
            distance: dictionary keyed by vertex of shortest distance from start_vertex to
            that vertex
            predecessor: dictionary keyed by vertex of previous vertex in shortest path
            from start_vertex
            negative_cycle: None if no negative cycle, otherwise an edge (u, v)

        """

        INF = float('inf')

        # init distances from start_vertex to all others as inf
        dist = {k: INF for k in self.graph}
        dist[start_vertex] = 0
        prev = {k: None for k in self.graph}

        # relax all edges num_vertices - 1 times
        for i in range(self.num_vertices - 1):
            for currency_a in self.graph:
                for currency_b in self.graph[currency_a]:
                    edge_wt = self.graph[currency_a][currency_b][PRICE]
                    # print(currency_a, currency_b, edge_wt)

                    # update the dist between currencies if the path is shorter
                    if dist[currency_a] is not INF:
                        if (tolerance + dist[currency_a] + edge_wt < dist[currency_b]) \
                                and (dist[currency_a] + edge_wt - tolerance < dist[
                            currency_b]):
                            dist[currency_b] = dist[currency_a] + edge_wt
                            prev[currency_b] = currency_a

        for currency_a in self.graph:
            for currency_b in self.graph[currency_a]:
                edge_wt = self.graph[currency_a][currency_b][PRICE]
                if (tolerance + dist[currency_a] + edge_wt < dist[currency_b]) \
                        and (dist[currency_a] + edge_wt - tolerance < dist[currency_b]):
                    return dist, prev, (currency_a, currency_b)

        return dist, prev, None

