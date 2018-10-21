#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os


class ElectricalNetwork:

    def __init__(self, buses, branches):

        self.buses = buses
        self.branches = branches

    def save(self, save_folder):
        self.buses.to_csv(os.path.join(save_folder, 'buses.csv'), index_label='id')
        self.branches.to_csv(os.path.join(save_folder, 'branches.csv'), index_label='id')
