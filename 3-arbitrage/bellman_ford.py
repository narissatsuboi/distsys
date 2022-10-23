"""
Bellman-Ford Implementation
:authors: Narissa Tsuboi
:version: 1
"""

import fxp_bytes_subscriber  # for data import


class BellmanFord(object):

    def __init__(self, data):
        self.graph = []
        self.num_vertices = len(data)
        self.exchange_dict = data  # nested dict representing vert : {edge to: dist, ...}

    # TODO maintain set of active vertices? does this come from the subscriber?
    def add_edge(self, start_vertex, end_vertex, edge_dist):
        self.graph.append([start_vertex, end_vertex, edge_dist])

    def populate_graph(self):
        for start_vertex, other_vertices in self.exchange_dict.items():
            for end_vertex in other_vertices:
                self.add_edge(start_vertex, end_vertex, other_vertices[end_vertex])

        print(self.graph)

    def run(self):
        self.populate_graph()

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

    # list of vertices
    # relax every node number of vertices - 1 times

if __name__ == '__main__':
    print('\n/// Belman Ford ///')
    exchanges = {
                    'a': {'b': 1, 'c':5}, 'b': {'c': 2, 'a': 10},
                    'c': {'a': 14, 'd': -3}, 'e': {'a': -200}
                  }

    mybf = BellmanFord(exchanges)
    mybf.run()
    mybf.print_graph()