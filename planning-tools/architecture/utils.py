#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np


def tsp_solver(points, costmatrix, init):
    """ Calculate the shortest path containing a set of geographical nodes,
    with a, initial solution.

    :param points:
        set of geographical nodes that have to be connected.

    :param costmatrix:
        matrix containing the cost of the path for each pair of nodes.

    :param init:
        initial solution which necessitates at least two nodes or more.

    :return:
        the shortest path and its cost.

    """

    # Verify the input
    try:
        assert len(init) >= 2
    except AssertionError:
        print("The travelling salesman problem needs at least two points for "
              "the initial solution. The returned path is not optimized!")
        return points, np.inf

    # Set the points to connect and the initial solution
    path = init
    xprim = init
    pts = points

    # Algorithm of Christofides
    while list(set(pts) - set(xprim)):
        xent = list(set(pts) - set(xprim))
        d_min = [0] * len(xent)
        id_min = [0] * len(xent)
        ia_min = [0] * len(xent)
        d = [0] * len(xprim)

        for i in range(0, len(xent)):
            for j in range(0,len(xprim)):
                d[j] = costmatrix[min([xent[i], xprim[j]]), max([xent[i], xprim[j]])]
            d_min[i] = min(d)
            position = d.index(d_min[i])
            id_min[i] = xent[i]
            ia_min[i] = xprim[position]

        position = d_min.index(max(d_min))
        n = [int(ia_min[position]), int(id_min[position])]
        dmin = np.inf
        for i in range(0, len(path)-1):
            new_d = costmatrix[min([path[i], n[1]]), max([path[i], n[1]])] + \
                    costmatrix[min([n[1], path[i+1]]), max([n[1], path[i+1]])] - \
                    costmatrix[min([path[i], path[i+1]]), max([path[i], path[i+1]])]
            if new_d < dmin:
                dmin = new_d
                order = i

        path = path[:(order + 1)] + [n[1]] + path[(order + 1):]
        xprim.append(n[1])

    # Cost of the path
    cost = 0
    for i in range(0, len(path) - 1):
        cost += costmatrix[min([path[i], path[i + 1]]), max([path[i], path[i + 1]])]

    # Create and return of the optimized path
    return path, cost