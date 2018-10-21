#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging

import pandas as pd

logger = logging.getLogger(__name__)


def read_architecture_files(hv_mv_substations_filename, mv_lv_substations_filename):
    # Read the CSV files
    hv_mv_substations = pd.read_csv(hv_mv_substations_filename, index_col='id')
    logger.info('Extraction of the HV/MV substations: {!r} substations.'.format(len(hv_mv_substations)))
    mv_lv_substations = pd.read_csv(mv_lv_substations_filename, index_col='id')
    logger.info('Extraction of the MV/LV substations: '
                '{!r} substations for {:.2f} MW.'.format(len(mv_lv_substations), mv_lv_substations['P (MW)'].sum()))

    return hv_mv_substations, mv_lv_substations


def read_sizing_files(buses_filename, branches_filename):
    # Read the CSV files
    buses = pd.read_csv(buses_filename, index_col='id')
    logger.info('Extraction of {!r} electrical buses for {:.2f} MVA.'.format(len(buses), buses['s'].sum()))
    branches = pd.read_csv(branches_filename, index_col='id')
    logger.info('Extraction of {!r} branches for {:.2f} km.'.format(len(branches), branches['length'].sum()))

    return buses, branches
