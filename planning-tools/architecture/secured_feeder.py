#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import random
import time

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from ..electrical_network.electrical_network import ElectricalNetwork

from .utils import tsp_solver

logger = logging.getLogger(__name__)

# Parameters of the simulated annealing
N_0 = 100
TAU_0 = 0.5
ALPHA = 0.9
N_1 = 12
N_2 = 100
N_3 = 5


class SecuredFeeder:

    def __init__(self, hv_mv_substations, mv_lv_substations, feeders=None, x=None, buses=None, branches=None):
        """Description of a secured feeder architecture.

        Args:
            hv_mv_substations (pandas.DataFrame):
                The data frame of HV/MV substations.

            mv_lv_substations (pandas.DataFrame):
                The data frame of MV/LV substations.

            feeders (pandas.DataFrame):
                The data frame of MV feeders.

            x (Dict):
                A dictionary associating each substations to a feeder.

            buses (pandas.DataFrame):
                The data frame of electrical buses.

            branches (pandas.DataFrame):
                The data frame of electrical buses.

        """

        # HV/MV and MV/LV substations
        if buses is None:
            buses_dict = {'id': [], 'name': [], 'type': [], 's': [], 'x': [], 'y': [], 'feeder': []}
            idx_bus = 1
            for index, row in hv_mv_substations.iterrows():
                buses_dict['id'].append(idx_bus)
                buses_dict['name'].append('hv' + str(index))
                buses_dict['type'].append('hv_source')
                buses_dict['s'].append(None)
                buses_dict['x'].append(row['x'])
                buses_dict['y'].append(row['y'])
                buses_dict['feeder'].append(None)
                idx_bus += 1
            for index, row in mv_lv_substations.iterrows():
                buses_dict['id'].append(idx_bus)
                buses_dict['name'].append('mv' + str(index))
                buses_dict['type'].append('mv_load')
                buses_dict['s'].append(row['P (MW)'])
                buses_dict['x'].append(row['x'])
                buses_dict['y'].append(row['y'])
                if x is None:
                    buses_dict['feeder'].append(0)
                else:
                    buses_dict['feeder'].append(x[index])
                idx_bus += 1
            self.buses = pd.DataFrame(buses_dict)
            self.buses = self.buses.set_index('id')
        else:
            self.buses = buses

        # Branches
        if branches is None:
            branches_dict = {'id': [], 'name': [], 'bus1': [], 'bus2': [], 'type': [], 'type_name': [], 'length': [],
                             'state': [], 'feeder': []}
            self.branches = pd.DataFrame(branches_dict)
        else:
            self.branches = branches

        # MV feeders
        self.feeders = feeders
        self.feeders['bus1'] = 0
        self.feeders['bus2'] = 0
        self.feeders['length'] = 0
        self.feeders['nb_substations'] = 0
        self.path_feeders = dict()
        for index, row in self.feeders.iterrows():
            self.path_feeders[index] = 0
            self.feeders.loc[index, 'bus1'] = self.buses[self.buses['name'] == ('hv' + str(row['source1']))].index[0]
            self.feeders.loc[index, 'bus2'] = self.buses[self.buses['name'] == ('hv' + str(row['source2']))].index[0]

        # Distance between the points
        self.distances = dict()
        index = self.buses.index
        for i in range(0, len(self.buses) - 1):
            for j in range(i + 1, len(self.buses)):
                index_1 = index[i]
                index_2 = index[j]
                self.distances[index_1, index_2] = np.sqrt((self.buses['x'][index_1] - self.buses['x'][index_2]) ** 2
                                                           + (self.buses['y'][index_1] - self.buses['y'][index_2]) ** 2)

        # Electrical network
        self.electrical_network = ElectricalNetwork(buses=self.buses, branches=self.branches)

    def random_placement(self):
        for index, row in self.buses[self.buses['type'] == 'mv_load'].iterrows():
            rdm = random.randint(0, len(self.feeders) - 1)
            self.buses.loc[index, 'feeder'] = self.feeders.index[rdm]

    def optimize_feeders(self, list_of_feeders=None):
        # List of the feeder to study
        if list_of_feeders is None:
            list_of_feeders = self.feeders.index
        # Characteristics of the modified branches
        self.branches = self.branches.loc[~self.branches['feeder'].isin(list_of_feeders), :]
        branches_dict = {'id': [], 'name': [], 'bus1': [], 'bus2': [], 'type': [], 'type_name': [], 'length': [],
                         'state': [], 'feeder': []}
        # For each feeder, resolution of the travelling salesman problem
        for index in list_of_feeders:
            hv_points = [self.feeders.loc[index, 'bus1'], self.feeders.loc[index, 'bus2']]
            mv_points = list(self.buses[self.buses['feeder'] == index].index)
            points = list(hv_points)
            points.extend(mv_points)
            self.path_feeders[index], self.feeders.loc[index, 'length'] = tsp_solver(points=points,
                                                                                     costmatrix=self.distances,
                                                                                     init=hv_points)
            self.feeders.loc[index, 'nb_substations'] = len(mv_points)
            for ind in range(len(self.path_feeders[index]) - 1):
                bus1 = int(self.path_feeders[index][ind])
                bus2 = int(self.path_feeders[index][ind + 1])
                branches_dict['id'].append(ind)
                branches_dict['name'].append('feeder_{}_line_{}'.format(index, ind))
                branches_dict['bus1'].append(bus1)
                branches_dict['bus2'].append(bus2)
                branches_dict['type'].append('line')
                branches_dict['type_name'].append(None)
                branches_dict['length'].append(self.distances[min([bus1, bus2]), max([bus1, bus2])])
                branches_dict['state'].append(True)
                branches_dict['feeder'].append(index)
        self.branches = self.branches.append(pd.DataFrame(branches_dict))
        # Reindex branches
        self.branches.loc[:, 'id'] = range(len(self.branches))
        # Calculation of total length
        total_length = self.feeders['length'].sum()
        return total_length

    def generate_electrical_network(self):
        self.electrical_network = ElectricalNetwork(buses=self.buses, branches=self.branches)

    def display(self):
        figure = plt.figure()
        ax = plt.subplot()
        ax.axis('equal')
        ax.axis('off')
        for index, row in self.buses.iterrows():
            if row['type'] == 'hv_source':
                ax.plot(row['x'], row['y'], 'sk')
            else:
                ax.plot(row['x'], row['y'], 'or')
        for path in self.path_feeders.values():
            for i in range(len(path) - 1):
                ax.plot([self.buses['x'][path[i]], self.buses['x'][path[i + 1]]],
                        [self.buses['y'][path[i]], self.buses['y'][path[i + 1]]],
                        '-b')
        figure.tight_layout()


def simulated_annealing(architecture):
    """Optimize the architecture of secured feeder with an adapted simulated annealing.

    Args:
        architecture (SecuredFeeder):
            The description of the secured feeder architecture.

    Return:
        architecture (SecuredFeeder):
            The description of the secured feeder architecture optimized by simulated annealing.
    """

    # Characteristics of the architecture
    n_substations = len(architecture.buses[architecture.buses['type'] == 'mv_load'])
    index_substations = list(architecture.buses[architecture.buses['type'] == 'mv_load'].index)
    list_of_feeders = list(architecture.feeders.index)

    # Initialization
    architecture.random_placement()
    d_ini = architecture.optimize_feeders()
    delta_0 = list()
    while True:
        d_new, architecture, idx_substation, idx_feeder, new_idx_feeder = _elementary_change(architecture,
                                                                                             index_substations,
                                                                                             list_of_feeders)
        if d_new > d_ini:
            delta_0.append(d_new - d_ini)
        if len(delta_0) == N_0:
            break
    t_0 = -np.mean(delta_0) / np.log(TAU_0 / 100)

    # Optimization
    t = t_0
    ite = 0
    n_steps = 0  # number of temperature steps
    n_pos = 0  # number of positive modifications
    n_tot = 0  # number of total tentatives
    d_opt = [d_ini]
    x_opt = architecture.buses['feeder']
    logger.info('Begining of the optimization.')
    logger.info('Step {!r} : T = {:.0f}°'.format(n_steps, t_0))
    start = time.perf_counter()
    while True:
        try:
            # Elementary modification of the architecture
            d_new, architecture, idx_substation, idx_feeder, new_idx_feeder = _elementary_change(architecture,
                                                                                                 index_substations,
                                                                                                 list_of_feeders)
            logger.debug('New solution : {:.0f} m (Best solution {:.0f} m)'.format(d_new, d_opt[n_steps]))

            # Evaluation of the modification
            if d_new > d_ini:
                # The total length increases: Metropolis test
                r = random.random()
                if r > np.exp(-(d_new - d_ini) / t):
                    # Modification not accepted
                    architecture.buses.loc[idx_substation, 'feeder'] = idx_feeder
                    architecture.optimize_feeders(list_of_feeders=[idx_feeder, new_idx_feeder])
                else:
                    # Modification accepted
                    d_ini = d_new
            else:
                # The total length decreases: modification accepted
                d_ini = d_new
                n_pos += 1
                # Best solution
                if d_ini < d_opt[n_steps]:
                    d_opt[n_steps] = d_ini
                    x_opt = list(architecture.buses['feeder'])
                    logger.info('New optimum: {:.0f} meters.'.format(d_opt[n_steps]))
            n_tot += 1

            # Test for temperature step
            if n_pos >= N_1 * n_substations or n_tot >= N_2 * n_substations:
                d_opt.append(d_opt[n_steps])
                t *= ALPHA
                n_steps += 1
                logger.info('Step {!r} : T = {:.0f}°C ({!r} accepted / {!r})'.format(n_steps, t, n_pos, n_tot))
                n_pos = 0
                n_tot = 0

            # Test: end of the simulation
            if len(d_opt) > N_3:
                if d_opt[n_steps] == d_opt[n_steps - N_3 + 1]:
                    break
            if t < 1e-3:
                break

            ite += 1

        except KeyboardInterrupt:
            logger.warning('Optimization interrupted by the user.')
            break

    end = time.perf_counter()

    logger.info('End of the optimization ({:.2f} minutes).'.format((end - start) / 60))
    architecture.buses['feeder'] = x_opt
    architecture.optimize_feeders()

    return architecture


def _elementary_change(architecture, index_substations, list_of_feeders):
    # Elementary modification of the architecture
    idx_substation = random.choice(index_substations)
    idx_feeder = architecture.buses.loc[idx_substation, 'feeder']
    new_list_of_feeders = [x for x in list_of_feeders if x != idx_feeder]
    new_idx_feeder = random.choice(new_list_of_feeders)
    architecture.buses.loc[idx_substation, 'feeder'] = new_idx_feeder
    d_new = architecture.optimize_feeders(list_of_feeders=[idx_feeder, new_idx_feeder])
    architecture.generate_electrical_network()
    logger.debug('Moving substation {} from feeder {} to {}'.format(idx_substation, idx_feeder, new_idx_feeder))

    return d_new, architecture, idx_substation, idx_feeder, new_idx_feeder
