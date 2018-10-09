#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Read files
----------

This `read_gis_files` function of this file read files that are used to extract the electrical network from the
geographic information system files. It also read auxiliary files such as reference type lines database or city files.
"""

import logging

import pandas as pd

logger = logging.getLogger(__name__)


def read_files(hv_mv_substations_filename, mv_lv_substations_filename):
    # Read the CSV files
    hv_mv_substations = pd.read_csv(hv_mv_substations_filename)
    logger.info('Extraction of the HV/MV substations: {} substations.'.format(len(hv_mv_substations)))
    mv_lv_substations = pd.read_csv(mv_lv_substations_filename)
    logger.info('Extraction of the MV/LV substations: '
                '{} substations for {:.2f} MW.'.format(len(mv_lv_substations), mv_lv_substations['P (MW)'].sum()))

    return hv_mv_substations, mv_lv_substations
