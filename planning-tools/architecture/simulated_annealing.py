#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import time
from random import randint, random

import numpy as np

logger = logging.getLogger(__name__)

# Parameters of the simulated annealing
N_0 = 100
TAU_0 = 0.5
ALPHA = 0.9
N_1 = 12
N_2 = 100
N_3 = 5


def simulated_annealing(architecture):
    # Characteristics of the architecture
    n_substations = len(architecture.nodes[architecture.nodes['type'] == 'MV'])
    index_substations = list(architecture.nodes[architecture.nodes['type'] == 'MV'].index)
    n_feeders = len(architecture.feeders)
    list_of_feeders = list(architecture.feeders.keys())

    # Initialization
    architecture.random_placement()
    d_ini = architecture.optimize_feeders()
    delta_0 = list()
    while True:
        d_new, idx_substation, idx_feeder = _elementary_change(architecture, index_substations, list_of_feeders)
        if d_new > d_ini:
            delta_0.append(d_new - d_ini)
        if len(delta_0) == N_0:
            break
    t_0 = -np.mean(delta_0) / np.log(TAU_0 / 100)
    logger.info('Initial temperature: {}'.format(t_0))

    # Optimization
    t = t_0
    ite = 0
    n_steps = 0  # number of temperature steps
    n_pos = 0  # number of positive modifications
    n_tot = 0  # number of total tentatives
    d_opt = list()
    d_opt.append(d_ini)
    logger.info('Begining of the optimization: T = {:.0f}°C'.format(t))
    start = time.perf_counter()
    while True:
        try:
            # Elementary modification of the architecture
            d_new, idx_substation, idx_feeder = _elementary_change(architecture, index_substations, list_of_feeders)
            logger.debug('New solution : {:.0f} m (Best solution {:.0f} m)'.format(d_new, d_opt[n_steps]))

            # Best solution
            if d_ini < d_opt[n_steps]:
                d_opt[n_steps] = d_ini
                logger.info('New optimum: {:.0f} meters.'.format(d_opt[n_steps]))

            # Evaluation of the modification
            if d_new > d_ini:
                # The total length increases: Metropolis test
                r = random()
                if r > np.exp(-(d_new - d_ini) / t):
                    # Modification not accepted
                    architecture.nodes.loc[idx_substation, 'feeder'] = idx_feeder
                else:
                    # Modification accepted
                    d_ini = d_new
            else:
                # The total length decreases: modification accepted
                d_ini = d_new
                n_pos += 1
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
            if len(d_opt) == N_3:
                if d_opt[n_steps] == d_opt[n_steps - N_3 + 1]:
                    break

            ite += 1

        except KeyboardInterrupt:
            logger.warning('Optimization interrupted by the user.')
            break

    end = time.perf_counter()

    logger.info('End of the optimization ({:.2f} minutes).'.format((end - start) / 60))

    return architecture


def _elementary_change(architecture, index_substations, list_of_feeders):
    # Elementary modification of the architecture
    idx_substation = index_substations[randint(0, len(index_substations) - 1)]
    idx_feeder = architecture.nodes.loc[idx_substation, 'feeder']
    new_list_of_feeders = [x for x in list_of_feeders if x != idx_feeder]
    new_idx_feeder = new_list_of_feeders[randint(0, len(new_list_of_feeders) - 1)]
    architecture.nodes.loc[idx_substation, 'feeder'] = new_idx_feeder
    d_new = architecture.optimize_feeders(list_of_feeders=[idx_feeder, new_idx_feeder])
    logger.debug('Moving substation {} from feeder {} to {}'.format(idx_substation, idx_feeder, new_idx_feeder))

    return d_new, idx_substation, idx_feeder
