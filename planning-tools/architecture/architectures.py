#!/usr/bin/env python
# -*- coding: utf-8 -*-

import random

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt

from .utils import tsp_solver


class SecuredFeeder:

    def __init__(self, hv_mv_substations, mv_lv_substations, pairing=None, x=None, nodes=None):
        """Description of a secured feeder architecture.

                Args:
                    hv_mv_substations (pandas.DataFrame):
                        The data frame of HV/MV substations.

                    mv_lv_substations (pandas.DataFrame):
                        The data frame of MV/LV substations.

                    x (Dict):
                        A dictionary associating each substations to a feeder.

                    pairing (List):
                        List of pairs between HV/MV substations
                """
        # HV/MV and MV/LV substations
        if nodes is None:
            nodes_dict = {'id': [], 'type': [], 's': [], 'x': [], 'y': [], 'feeder': []}
            for index, row in hv_mv_substations.iterrows():
                nodes_dict['id'].append(index)
                nodes_dict['type'].append('HV')
                nodes_dict['s'].append(None)
                nodes_dict['x'].append(row['x'])
                nodes_dict['y'].append(row['y'])
                nodes_dict['feeder'].append(None)
            for index, row in mv_lv_substations.iterrows():
                nodes_dict['id'].append(index)
                nodes_dict['type'].append('MV')
                nodes_dict['s'].append(row['P (MW)'])
                nodes_dict['x'].append(row['x'])
                nodes_dict['y'].append(row['y'])
                if x is None:
                    nodes_dict['feeder'].append(0)
                else:
                    nodes_dict['feeder'].append(x[index])
            self.nodes = pd.DataFrame(nodes_dict)
        else:
            self.nodes = nodes

        # Pairing between HV/MV substations
        if pairing is None:
            self.pairing = dict()
            index = 1
            for i in range(0, len(hv_mv_substations) - 1):
                for j in range(i + 1, len(hv_mv_substations)):
                    self.pairing[index] = [hv_mv_substations.index[i], hv_mv_substations.index[j]]
                    index += 1
        else:
            self.pairing = pairing

        # Path of each feeder
        self.feeders = dict()
        self.lengths = dict()
        for idx_feeder in self.pairing.keys():
            self.feeders[idx_feeder] = list()
            self.lengths[idx_feeder] = 0

        # Distance between the points
        self.distances = dict()
        idx = self.nodes.index
        for i in range(0, len(self.nodes) - 1):
            for j in range(i + 1, len(self.nodes)):
                idx_1 = idx[i]
                idx_2 = idx[j]
                self.distances[idx_1, idx_2] = np.sqrt((self.nodes['x'][idx_1] - self.nodes['x'][idx_2]) ** 2
                                                       + (self.nodes['y'][idx_1] - self.nodes['y'][idx_2]) ** 2)

    def random_placement(self):
        for index, row in self.nodes[self.nodes['type'] == 'MV'].iterrows():
            self.nodes.loc[index, 'feeder'] = random.randint(1, len(self.pairing))

    def optimize_feeders(self, list_of_feeders=None):
        if list_of_feeders is None:
            list_of_feeders = self.pairing.keys()
        for idx_feeder in list_of_feeders:
            hv_points = self.nodes[self.nodes['type'] == 'HV']
            hv_points = hv_points[hv_points['id'].isin(self.pairing[idx_feeder])]
            mv_points = self.nodes[self.nodes['feeder'] == idx_feeder]
            points = list(hv_points.index) + list(mv_points.index)
            self.feeders[idx_feeder], self.lengths[idx_feeder] = tsp_solver(points=points,
                                                                            costmatrix=self.distances,
                                                                            init=list(hv_points.index))
        total_length = np.sum(list(self.lengths.values()))
        return total_length

    def display(self):
        figure = plt.figure()
        ax = plt.subplot()
        ax.axis('equal')
        ax.axis('off')
        for index, row in self.nodes.iterrows():
            if row['type'] == 'HV':
                ax.plot(row['x'], row['y'], 'sk')
            else:
                ax.plot(row['x'], row['y'], 'or')
        for feeder in self.feeders.values():
            for i in range(len(feeder) - 1):
                ax.plot([self.nodes['x'][feeder[i]], self.nodes['x'][feeder[i + 1]]],
                        [self.nodes['y'][feeder[i]], self.nodes['y'][feeder[i + 1]]],
                        '-b')
        figure.tight_layout()
