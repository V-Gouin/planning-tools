#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import os

import click
from matplotlib import pyplot as plt

from .architecture.secured_feeder import SecuredFeeder, simulated_annealing
import pandas as pd
from .io.read_files import read_files
from .log_utils import CLICKVERBOSITY, set_logging_config

logger = logging.getLogger(__name__)

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'], max_content_width=120)
EPILOG = 'Set of tools for the planning of electrical distribution networks.'


@click.group(name='planning-tools', epilog=EPILOG, context_settings=CONTEXT_SETTINGS,
             help="Set of tools for the planning of electrical distribution networks.")
@click.option('--verbosity', type=CLICKVERBOSITY, help='The verbosity level', default=None)
@click.pass_context
def planning_tools(ctx, verbosity):
    if ctx.obj is None:
        ctx.obj = dict()
    if verbosity is not None:
        ctx.obj['verbosity'] = verbosity


@planning_tools.command(help="Build the MV architecture of the electrical distribution network.",
                        epilog=EPILOG, context_settings=CONTEXT_SETTINGS)
@click.argument('hv_mv_substations_filename', type=click.Path(exists=True), nargs=1)
@click.argument('mv_lv_substations_filename', type=click.Path(exists=True), nargs=1)
@click.option('--feeders-file', '-f', type=click.Path(exists=False, file_okay=True, dir_okay=True),
              default=None, help='Configuration of the MV feeders. The default is \'None\'.')
@click.option('--verbosity', type=CLICKVERBOSITY, help='The verbosity level. The default is \'info\'.', default='info')
@click.option('--output-folder', '-o', type=click.Path(exists=False, file_okay=False, dir_okay=True),
              default='Results', help='The folder to export the results of the extraction. The default is \'Results\'.')
@click.pass_context
def architecture(ctx, hv_mv_substations_filename, mv_lv_substations_filename, feeders_file, verbosity, output_folder):
    #
    # Activate the log
    #
    if 'verbosity' in ctx.obj:
        verbosity = ctx.obj['verbosity']
    set_logging_config(verbosity=verbosity, filename=os.path.join(output_folder, 'extraction.log'))
    logger.info('Begining of the program.')

    #
    # Read the input file
    #
    hv_mv_substations, mv_lv_substations = read_files(hv_mv_substations_filename, mv_lv_substations_filename)

    #
    # Configuration of the MV feeders
    #
    if feeders_file is None:
        feeders_dict = ({'id': [], 'name': [], 'source1': [], 'source2': []})
        idx = 1
        for i in range(0, len(hv_mv_substations) - 1):
            for j in range(i + 1, len(hv_mv_substations)):
                feeders_dict['id'].append(idx)
                feeders_dict['name'].append('feeder_' + str(idx))
                feeders_dict['source1'].append(hv_mv_substations.index[i])
                feeders_dict['source2'].append(hv_mv_substations.index[j])
                idx += 1
        feeders = pd.DataFrame(feeders_dict)
        feeders = feeders.set_index('id')
    else:
        feeders = pd.read_csv(feeders_file, index_col='id')

    #
    # Build the architecture
    #
    secured_feeder = SecuredFeeder(hv_mv_substations=hv_mv_substations,
                                   mv_lv_substations=mv_lv_substations,
                                   feeders=feeders)
    secured_feeder_opt = simulated_annealing(secured_feeder)
    print(secured_feeder_opt.electrical_network.branches)
    print(secured_feeder_opt.feeders)
    plt.close('all')
    secured_feeder_opt.display()
    plt.show()
    #
    # nodes = pd.read_csv('Results/secured_feeder.csv')
    # secured_feeder_opt = SecuredFeeder(hv_mv_substations=hv_mv_substations,
    #                                    mv_lv_substations=mv_lv_substations,
    #                                    pairing=pairing,
    #                                    nodes=nodes)
    # secured_feeder_opt.optimize_feeders()
    # secured_feeder_opt.display()
    # plt.show()


if __name__ == '__main__':
    planning_tools(obj={}, prog_name='planning-tools')
