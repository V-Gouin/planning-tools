#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import os

import click
import pandas as pd

from .architecture.secured_feeder import SecuredFeeder, simulated_annealing
from .electrical_network.electrical_network import ElectricalNetwork
from .io.read_files import read_architecture_files, read_sizing_files
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
    hv_mv_substations, mv_lv_substations = read_architecture_files(hv_mv_substations_filename, mv_lv_substations_filename)

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
    secured_feeder = simulated_annealing(secured_feeder)

    # Generate the electrical network
    electrical_network = ElectricalNetwork(buses=secured_feeder.buses, branches=secured_feeder.branches)
    electrical_network.save(output_folder)


@planning_tools.command(help="Perform the sizing of the electrical network based on its architecture and"
                             "technical-economicals parameters.",
                        epilog=EPILOG, context_settings=CONTEXT_SETTINGS)
@click.argument('buses_filename', type=click.Path(exists=True), nargs=1)
@click.argument('branches_filename', type=click.Path(exists=True), nargs=1)
@click.option('--verbosity', type=CLICKVERBOSITY, help='The verbosity level. The default is \'info\'.', default='info')
@click.option('--output-folder', '-o', type=click.Path(exists=False, file_okay=False, dir_okay=True),
              default=None, help='The folder to export the results of the sizing. If no path is provided, the input'
                                 'files are overwritten with the results.')
@click.pass_context
def sizing(ctx, buses_filename, branches_filename, verbosity, output_folder):
    #
    # Activate the log
    #
    if 'verbosity' in ctx.obj:
        verbosity = ctx.obj['verbosity']
    if output_folder is None:
        output_folder = os.path.dirname(buses_filename)
    set_logging_config(verbosity=verbosity, filename=os.path.join(output_folder, 'sizing.log'))
    logger.info('Begining of the program.')

    #
    # Read the input file
    #
    buses, branches = read_sizing_files(buses_filename, branches_filename)

    # Generate the electrical network
    electrical_network = ElectricalNetwork(buses=buses, branches=branches)
    electrical_network.save(output_folder)


if __name__ == '__main__':
    planning_tools(obj={}, prog_name='planning-tools')
