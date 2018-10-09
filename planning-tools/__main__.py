#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import os

import click
from matplotlib import pyplot as plt

from .architecture.architectures import SecuredFeeder
import pandas as pd
from .architecture.simulated_annealing import simulated_annealing
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
@click.option('--verbosity', type=CLICKVERBOSITY, help='The verbosity level. The default is \'info\'.', default='info')
@click.option('--output-folder', '-o', type=click.Path(exists=False, file_okay=False, dir_okay=True),
              default='Results', help='The folder to export the results of the extraction. The default is \'Results\'.')
@click.pass_context
def architecture(ctx, hv_mv_substations_filename, mv_lv_substations_filename, verbosity, output_folder):
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
    # Build the architecture
    #
    pairing = {1: [0, 1],
               2: [1, 2],
               3: [2, 0]}
    # pairing={1: [0, 1],
    #         2: [0, 1],
    #         3: [0, 1],
    #         4: [0, 2],
    #         5: [0, 2],
    #         6: [1, 2],
    #         7: [1, 2]}
    secured_feeder = SecuredFeeder(hv_mv_substations=hv_mv_substations,
                                   mv_lv_substations=mv_lv_substations,
                                   pairing=pairing)
    secured_feeder.random_placement()
    secured_feeder.optimize_feeders()
    secured_feeder.display()
    plt.show()

    secured_feeder_opt = simulated_annealing(secured_feeder)
    secured_feeder.nodes.to_csv('Results/secured_feeder.csv')
    secured_feeder_opt.display()
    plt.show()

    nodes = pd.read_csv('Results/secured_feeder.csv')
    secured_feeder_opt = SecuredFeeder(hv_mv_substations=hv_mv_substations,
                                       mv_lv_substations=mv_lv_substations,
                                       pairing=pairing,
                                       nodes=nodes)
    secured_feeder_opt.optimize_feeders()
    secured_feeder_opt.display()
    plt.show()


if __name__ == '__main__':
    planning_tools(obj={}, prog_name='planning-tools')
