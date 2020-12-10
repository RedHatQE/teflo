# -*- coding: utf-8 -*-
#
# Copyright (C) 2017 Red Hat, Inc.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
"""
    teflo.cli

    This module contains the code which creates teflo's command line
    interface structure.

    :copyright: (c) 2017 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""

import click
from . import __version__
from .teflo import Teflo
from .constants import TASKLIST, TASK_LOGLEVEL_CHOICES
from .helpers import validate_cli_scenario_option


def print_header():
    click.echo("-" * 50)
    click.echo("Teflo Framework v%s" % __version__)
    click.echo("Copyright (C) 2020, Red Hat, Inc.")
    click.echo("-" * 50)


@click.group()
@click.option("-v", "--verbose", count=True,
              help="Add verbosity to the commands.")
@click.version_option()
def teflo(verbose):
    """Teflo - (Test Execution Framework Libraries and Objects) \n
       It is an orchestration software that controls the flow of a set of testing scenarios.\n
       It was formerly known as Carbon
    """
    if verbose:
        click.echo('\n--- Verbose mode ON (verbosity %s)---\n' % verbose)


# @teflo.command()
def create():
    """Create a scenario configuration."""
    raise NotImplementedError


@teflo.command()
@click.option("-s", "--scenario",
              default=None,
              metavar="",
              help="Scenario definition file to be executed.")
@click.option("--list-labels",
              default=None,
              metavar="",
              is_flag=True,
              help="List all the labels and associated resources in the SDF")
@click.pass_context
def show(ctx, scenario, list_labels):
    """Show information about the scenario."""
    print_header()
    scenario_stream = validate_cli_scenario_option(ctx, scenario)
    # Create a new teflo compound
    cbn = Teflo(__name__)

    # Sending the list of scenario streams to the teflo object
    cbn.load_from_yaml(scenario_stream)

    if list_labels:
        cbn.list_labels()
    else:
        click.echo('An option needs to be given. See help')
        ctx.exit()


@teflo.command()
@click.option("-s", "--scenario",
              default=None,
              metavar="",
              help="Scenario definition file to be executed.")
@click.option("-d", "--data-folder",
              default=None,
              metavar="",
              help="Directory for saving teflo runtime files.")
@click.option("-w", "--workspace",
              default=None,
              metavar="",
              help="Scenario workspace.")
@click.option("--log-level",
              type=click.Choice(TASK_LOGLEVEL_CHOICES),
              default=None,
              help="Select logging level. (default=info)")
@click.option("--vars-data",
              default=None,
              metavar="",
              help="Pass in variable data to template the scenario. Can be a file or raw json.")
@click.option("-l", "--labels",
              default=None,
              metavar="",
              multiple=True,
              type=str,
              help="Use only the resources associated with labels for running the tasks. "
                   "labels and skip_labels are mutually exclusive")
@click.option("-sl", "--skip-labels",
              default=None,
              metavar="",
              type=str,
              multiple=True,
              help="Skip the resources associated with skip_labels for running the tasks. "
                   "labels and skip_labels are mutually exclusive")
@click.option("-sn", "--skip-notify",
              default=None,
              metavar="",
              type=str,
              multiple=True,
              help="Skip triggering the specific notification defined for the scenario."
              )
@click.option("-nn", "--no-notify",
              is_flag=True,
              metavar="",
              help="Disable sending an notifications defined for the scenario."
              )
@click.pass_context
def validate(ctx, scenario, data_folder, log_level, workspace, vars_data, labels, skip_labels, skip_notify, no_notify):
    """Validate a scenario configuration."""

    scenario_stream = validate_cli_scenario_option(ctx, scenario, vars_data)

    # checking if labels or skip_labels both are set
    if labels and skip_labels:
        click.echo('Labels and skip_labels are mutually exclusive. Only one of them can be used')
        ctx.exit()

    cbn = Teflo(
        __name__,
        log_level=log_level,
        data_folder=data_folder,
        workspace=workspace,
        labels=labels,
        skip_labels=skip_labels,
        skip_notify=skip_notify,
        no_notify=no_notify
    )

    # This is the easiest way to configure a full scenario.
    cbn.load_from_yaml(scenario_stream)

    # The scenario will start the main pipeline and run through the ordered
    # list of pipelines. See :function:`~teflo.Teflo.run` for more details.
    cbn.run(tasklist=["validate"])


@teflo.command()
@click.option("-t", "--task",
              default=None,
              type=click.Choice(TASKLIST),
              multiple=True,
              help="Select task to run. (default=all)")
@click.option("-s", "--scenario",
              default=None,
              metavar="",
              help="Scenario definition file to be executed.")
@click.option("-d", "--data-folder",
              default=None,
              metavar="",
              help="Directory for saving teflo runtime files.")
@click.option("-w", "--workspace",
              default=None,
              metavar="",
              help="Scenario workspace.")
@click.option("--log-level",
              type=click.Choice(TASK_LOGLEVEL_CHOICES),
              default=None,
              help="Select logging level. (default=info)")
@click.option("--vars-data",
              default=None,
              metavar="",
              help="Pass in variable data to template the scenario. Can be a file or raw json.")
@click.option("-l", "--labels",
              default=None,
              metavar="",
              multiple=True,
              type=str,
              help="Use only the resources associated with labels for running the tasks. "
                   "labels and skip_labels are mutually exclusive")
@click.option("-sl", "--skip-labels",
              default=None,
              metavar="",
              type=str,
              multiple=True,
              help="Skip the resources associated with skip_labels for running the tasks. "
                   "labels and skip_labels are mutually exclusive")
@click.option("-sn", "--skip-notify",
              default=None,
              metavar="",
              type=str,
              multiple=True,
              help="Skip triggering the specific notification defined for the scenario."
              )
@click.option("-nn", "--no-notify",
              is_flag=True,
              metavar="",
              help="Disable sending an notifications defined for the scenario."
              )
@click.pass_context
def run(ctx, task, scenario, log_level, data_folder, workspace, vars_data, labels, skip_labels, skip_notify, no_notify):
    """Run a scenario configuration."""
    print_header()

    scenario_stream = validate_cli_scenario_option(ctx, scenario, vars_data)

    # checking if labels or skip_labels both are set
    if labels and skip_labels:
        click.echo('Labels and skip_labels are mutually exclusive. Only one of them can be used')
        ctx.exit()

    # Create a new teflo compound
    cbn = Teflo(
        __name__,
        log_level=log_level,
        data_folder=data_folder,
        workspace=workspace,
        labels=labels,
        skip_labels=skip_labels,
        skip_notify=skip_notify,
        no_notify=no_notify
    )

    # Sending the list of scenario streams to the teflo object
    cbn.load_from_yaml(scenario_stream)

    # Setup the list of tasks to run
    if not task:
        task = TASKLIST
    else:
        task = list(task)

    # The scenario will start the main pipeline and run through the task
    # pipelines declared. See :function:`~teflo.Teflo.run` for more details.
    cbn.run(tasklist=task)


@teflo.command()
@click.option("-s", "--scenario",
              default=None,
              metavar="",
              help="Scenario definition file to be executed.")
@click.option("-d", "--data-folder",
              default=None,
              metavar="",
              help="Directory for saving teflo runtime files.")
@click.option("-w", "--workspace",
              default=None,
              metavar="",
              help="Scenario workspace.")
@click.option("--log-level",
              type=click.Choice(TASK_LOGLEVEL_CHOICES),
              default=None,
              help="Select logging level. (default=info)")
@click.option("--vars-data",
              default=None,
              metavar="",
              help="Pass in variable data to template the scenario. Can be a file or raw json.")
@click.option("-sn", "--skip-notify",
              default=None,
              metavar="",
              type=str,
              multiple=True,
              help="Skip triggering the specific notification defined for the scenario."
              )
@click.option("-nn", "--no-notify",
              is_flag=True,
              metavar="",
              help="Disable sending an notifications defined for the scenario."
              )
@click.pass_context
def notify(ctx, scenario, log_level, data_folder, workspace, vars_data, skip_notify, no_notify):
    """Trigger notifications marked on demand for a scenario configuration."""
    print_header()

    scenario_stream = validate_cli_scenario_option(ctx, scenario, vars_data)

    # Create a new teflo compound
    cbn = Teflo(
        __name__,
        log_level=log_level,
        data_folder=data_folder,
        workspace=workspace,
        skip_notify=skip_notify,
        no_notify=no_notify
    )

    # Sending the list of scenario streams to the teflo object
    cbn.load_from_yaml(scenario_stream)

    # The scenario will start the main pipeline and run through the task
    # pipelines declared. See :function:`~teflo.Teflo.run` for more details.
    cbn.notify('on_demand')
