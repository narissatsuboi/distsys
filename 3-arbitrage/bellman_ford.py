"""
Bellman-Ford Implementation
:authors: Narissa Tsuboi
:version: 1
"""
from math import log


class BellmanFord(object):

    def __init__(self, data):
        """ Inits a new instance of the Bellman Ford algorithm on data passed in thru
        the object constructor.
        """
        # nested dict vert : {edge to: dist, ...}
        self.exchange_dict = data

        # list of vertices in graph
        self.vertices = set(self.exchange_dict.keys())

        # holds vertex lists representing analysis space
        self.graph = []

        # holds the current number of distinct vertices
        self.num_vertices = len(data)

    def run(self):
        self.populate_graph()

    # TODO maintain set of active vertices? does this come from the subscriber?
    def add_edge(self, start_vertex, end_vertex, edge_dist):
        """

        """
        # take the negative log of the exchange rate per BF algorithm
        edge_dist = -1 * log(edge_dist)

        # add new data point to graph
        self.graph.append([start_vertex, end_vertex, edge_dist])

    def populate_graph(self):
        """ Appends vertices and their edge information to the graph list. Per Bellman
        Floyd algorithm for arbitrage implementation, takes the negative log of each
        currency prior to adding to the graph.
        """
        for start_vertex, other_vertices in self.exchange_dict.items():
            for end_vertex in other_vertices:
                # add new edge to graph
                self.add_edge(start_vertex, end_vertex, other_vertices[end_vertex])

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
        neg_edge = None

        # init distances from start_vertex to all others as inf
        dist = {k: INF for k in self.vertices}
        dist[start_vertex] = 0

        # relax all edges num_vertices - 1 times
        for _ in range(self.num_vertices - 1):
            for start_vertex, end_vertex, edge_distance in self.graph:
                if dist[start_vertex] != INF and dist[end_vertex] + \
                        edge_distance < dist[end_vertex]:
                    dist[end_vertex] = dist[start_vertex] + edge_distance

        # check for negative cycles
        for start_vertex, end_vertex, edge_distance in self.graph:
            if dist[start_vertex] != INF and dist[start_vertex] + \
                    edge_distance < dist[end_vertex]:
                print('Graph contains negative weight cycle')
                neg_edge = (start_vertex, end_vertex)

        return neg_edge


if __name__ == '__main__':
    print('\n/// Belman Ford ///')
    exchanges = {
        'a': {'b': 1, 'c': 5}, 'b': {'c': 2, 'a': 10},
        'c': {'a': 14, 'd': 3}, 'e': {'a': 200}
    }

    mybf = BellmanFord(exchanges)
    mybf.run()
    print(mybf.graph)
    mybf.shortest_paths('a')
