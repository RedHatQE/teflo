# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 Red Hat, Inc.
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
    teflo

    Teflo a framework to test product interoperability.

    :copyright: (c) 2021 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""
from copy import deepcopy
import errno
from logging import root
import os
from re import L
import sys
from teflo.exceptions import TefloScenarioFailure
import blaster
import termcolor
from contextlib import ExitStack
from functools import partial
import yaml
import click
import shutil
from distutils.dir_util import copy_tree
from teflo.helpers import exec_local_cmd
from . import __name__ as __teflo_name__
from .constants import NOTIFYSTATES, TASKLIST, RESULTS_FILE, DATA_FOLDER, DEFAULT_INVENTORY
from .core import TefloError, LoggerMixin, TimeMixin, Inventory
from .helpers import file_mgmt, gen_random_str, sort_tasklist, preproc_path
from .resources import Scenario, Asset, Action, Report, Execute, Notification
from .utils.config import Config
from .utils.scenario_graph import ScenarioGraph
from .utils.pipeline import PipelineFactory


class Teflo(LoggerMixin, TimeMixin):
    """
    The Teflo object acts as the central object. We call this object
    'the teflo compound'. Like in chemistry, a teflo molecule helps on the
    construction of compounds of other molecules. We can use this analogy
    to understand how Teflo object creates compounds of 'resources'.

    The valid resources for Teflo can be found at ~teflo.resources package.
    These resources have special connection with teflo, which allows teflo
    to run the resources tasks, without the need to understand each resource
    in depth. Think of all caron resources as instances that are blessed by
    Teflo object. A teflo compound can have as many resource as it can.

    Once a compound of resources is defined, the function ~self.run will
    take care of running all the tasks needed to have the compound of
    resources up and running.

    The Teflo object passes through 6 main stages:
    (see all types of tasks at ~teflo.tasks package)

    1. Validation - a pipeline of tasks instances of ValidationTask.
    2. Provision - a pipeline of tasks instances of ProvisionTask.
    3. Orchestrate - a pipeline of tasks instances of OrchestrateTask.
    4. Execute - a pipeline of tasks instances of ExecuteTask.
    5. Report - a pipeline of tasks instances of ReportTask.
    6. Cleanup - a pipeline of tasks instances of CleanupTask.

    Each resource can have its own set of tasks. Theses tasks will be
    loaded within the central pipeline, the ~self.pipelines object.
    """

    config = Config()

    def __init__(self, import_name=__teflo_name__, log_level=None,
                 data_folder=None, workspace=None, **kwargs):
        """Constructor.

        :param import_name: module name
        :type import_name: str
        :param log_level: logging level
        :type log_level: str
        :param data_folder: folder path for storing teflo runtime files
        :type data_folder: str
        :param workspace: scenario workspace for locating scenario files
        :type workspace: str
        """
        # The name of the package or module.  Do not change this once
        # it was set by the constructor.
        self.import_name = import_name

        self._uid = gen_random_str(10)

        # load configuration settings
        self.config.load()

        # assigning cli options to teflo_options property
        self._teflo_options = dict()
        for key, value in kwargs.items():
            if key == 'labels' and value:
                self._teflo_options['labels'] = value
            if key == 'skip_labels' and value:
                self._teflo_options['skip_labels'] = value
            if key == 'skip_notify' and value:
                self._teflo_options['skip_notify'] = value
            if key == 'no_notify' and value:
                self._teflo_options['no_notify'] = value
            # assigning cli iterate_method value to self.config['INCLUDED_SDF_ITERATE_METHOD']
            if key == 'iterate_method' and value:
                self.config['INCLUDED_SDF_ITERATE_METHOD'] = value
            if key == 'skip_fail':
                self._teflo_options['skip_fail'] = value

        if log_level:
            self.config['LOG_LEVEL'] = log_level

        # Set custom data folder, if data_folder is pass as parameter to Teflo
        if data_folder:
            self.config['DATA_FOLDER'] = data_folder

        # define the results folder
        self.config['RESULTS_FOLDER'] = os.path.join(
            self.config['DATA_FOLDER'], '.results')

        # define the artifacts folder under the results folder
        self.config['ARTIFACT_FOLDER'] = os.path.join(self.config.get('RESULTS_FOLDER'), 'artifacts')

        # create artifacts location
        if not os.path.exists(self.config['ARTIFACT_FOLDER']):
            os.makedirs(self.config['ARTIFACT_FOLDER'])

        self.static_inv_dir = False
        # Put inventory under teflo's result folder if data folder has the default config value
        if self.config['DATA_FOLDER'] != DATA_FOLDER and self.config['INVENTORY_FOLDER'] == DEFAULT_INVENTORY:
            self.config['INVENTORY_FOLDER'] = os.path.join(self.config['RESULTS_FOLDER'], 'inventory')
        else:
            # set the user defined static inventory path
            self.static_inv_dir = True

        # Generate the UID for the teflo life-cycle based on data_folder
        self.config['DATA_FOLDER'] = os.path.join(self.config['DATA_FOLDER'],
                                                  self.uid)

        # Why a results folder and a data folder? The data folder is a unique
        # folder that is created for each teflo execution. This folder will
        # contain files generated by teflo for that specific execution. What
        # if you want to run a certain task, then run another task all using
        # a results file stored in a previous teflo data folder? Well its hard
        # to determine the data folder since its a random unique folder name.
        # The results folder will save the last executed teflo task. This way
        # you can point your next teflo task to run the scenario file from
        # this given folder.
        # i.e.
        #   provision task and then want to run orchestrate separately
        #       - teflo run -s scenario.yml -t provision
        #       - teflo run -s /tmp/.results/results.yml -t orchestrate

        for f in [self.config['DATA_FOLDER'], self.config['RESULTS_FOLDER']]:
            try:
                if not os.path.exists(f):
                    os.makedirs(f)

                # Let's create the inventory directory in the results folder
                # if a static inventory folder is specified to avoid complexity
                # copying the inventory directory data

                if '.results' in f and self.static_inv_dir:
                    res_inv_dir = os.path.join(f, 'inventory')
                    if not os.path.exists(res_inv_dir):
                        os.makedirs(res_inv_dir)
            except (OSError, IOError) as ex:
                if ex.errno == errno.EACCES:
                    raise TefloError("You don't have permission to create '"
                                      "the data folder.")
                else:
                    raise TefloError('Error creating data folder - '
                                      '{0}'.format(ex))

        # configure loggers
        self.create_logger(__teflo_name__, self.config)
        # pykwalify logging disabled for too much logging
        # self.create_logger('pykwalify.core', self.config)

        # set the workspace attribute
        if workspace:
            self.workspace = workspace
        else:
            self.workspace = os.getcwd()
            self.logger.warning(
                'Scenario workspace was not set, therefore the workspace is '
                'automatically assigned to the current working directory. You '
                'may experience problems if files needed by teflo do not '
                'exists in the scenario workspace.'
            )

        self.config['WORKSPACE'] = self.workspace

        # creating one time inventory object
        self.cbn_inventory: Inventory = Inventory.get_instance(self.config, self._uid)

        self.scenario_graph = ScenarioGraph()

        # Updating the os.environ variables with TEFLO_DATA_FOLDER and TEFLO_RESULTS_FOLDER
        os.environ.update({'TEFLO_DATA_FOLDER': os.path.abspath(self.config.get('DATA_FOLDER')),
                           'TEFLO_RESULTS_FOLDER': os.path.abspath(self.config.get('RESULTS_FOLDER')),
                           'TEFLO_WORKSPACE': os.path.abspath(self.config.get('WORKSPACE'))
                           })

    @property
    def name(self):
        """The name of the application.  This is usually the import name
        with the difference that it's guessed from the run file if the
        import name is main.  This name is used as a display name when
        Teflo needs the name of the scenario.  It can be set and overridden
        to change the value.
        """
        if self.import_name == '__main__':
            fn = getattr(sys.modules['__main__'], '__file__', None)
            if fn is None:
                return '__main__'
            return os.path.splitext(os.path.basename(fn))[0]
        return self.import_name

    @property
    def uid(self):
        return self._uid

    @property
    def data_folder(self):
        return self.config['DATA_FOLDER']

    @property
    def results_file(self):
        return os.path.join(self.data_folder, RESULTS_FILE)

    @property
    def teflo_options(self):
        return self._teflo_options

    def _populate_scenario_resources(self, scenario_obj: Scenario, scenario_stream):

        scenario_data = yaml.safe_load(scenario_stream)
        pro_items = scenario_data.pop('provision', None)
        orc_items = scenario_data.pop('orchestrate', None)
        exe_items = scenario_data.pop('execute', None)
        rpt_items = scenario_data.pop('report', None)
        notify_items = scenario_data.pop('notifications', None)

        scenario_obj.load(scenario_data)

        scenario_obj.load_resources(Asset, pro_items)
        scenario_obj.load_resources(Action, orc_items)
        scenario_obj.load_resources(Execute, exe_items)
        scenario_obj.load_resources(Report, rpt_items)
        scenario_obj.load_resources(Notification, notify_items)

    def load_from_yaml(self, scenario_graph: ScenarioGraph):
        """
        This method load and populate all resources from
        the scenario graph, it also validate all labels
        for all nodes inside of the scenaio graph
        """
        # setting up master scenario
        self.scenario_graph = scenario_graph

        # Iterate using certain iterator, this is post-order traversal for a tree-liked graph
        sc: Scenario
        for sc in self.scenario_graph:
            # Add resources to sc objects
            self._populate_scenario_resources(sc, sc.yaml_data)
            self.scenario_graph.reload_resources_from_scenario(sc)
            # setting scenario_graph property to each scenario in the scenario_graph
            sc.__setattr__('scenario_graph', self.scenario_graph)

        self._validate_labels()

    def list_labels(self):
        """This method displays all the labels in the scenario"""
        res_label_dict = dict()
        # getting all labels from all resources in the scenario
        for res in self.scenario_graph.get_all_resources():
            res_label_dict[res] = dict(name=getattr(res, 'name'),
                                        labels=[lab for lab in getattr(res, 'labels')])
        self.logger.info('-' * 79)
        self.logger.info('SCENARIO LABELS'.center(79))
        self.logger.info('-' * 79)
        self.logger.info('PROVISION SECTION')
        self.logger.info('-' * 79)
        self.logger.info("{:<20} | {}".format('Resource Name', 'Labels'))
        self.logger.info('-' * 79)
        for key, value in res_label_dict.items():
            if isinstance(key, Asset):
                self.logger.info("{:<20} | {}".format(value['name'], value['labels']))
        self.logger.info('-' * 79)
        self.logger.info('ORCHESTRATE SECTION')
        self.logger.info('-' * 79)
        self.logger.info("{:<20} | {}".format('Resource Name', 'Labels'))
        self.logger.info('-' * 79)
        for key, value in res_label_dict.items():
            if isinstance(key, Action):
                self.logger.info("{:<20} | {}".format(value['name'], value['labels']))
        self.logger.info('-' * 79)
        self.logger.info('EXECUTE SECTION')
        self.logger.info('-' * 79)
        self.logger.info("{:<20} | {}".format('Resource Name', 'Labels'))
        self.logger.info('-' * 79)
        for key, value in res_label_dict.items():
            if isinstance(key, Execute):
                self.logger.info("{:<20} | {}".format(value['name'], value['labels']))
        self.logger.info('-' * 79)
        self.logger.info('REPORT SECTION')
        self.logger.info('-' * 79)
        self.logger.info("{:<20} | {}".format('Resource Name', 'Labels'))
        self.logger.info('-' * 79)
        for key, value in res_label_dict.items():
            if isinstance(key, Report):
                self.logger.info("{:<20} | {}".format(value['name'], value['labels']))

    def _validate_labels(self):
        """This method validates that the labels provided by the users are mentioned withing the SDF. If no labels match
        any used by the resources in the SDF/scenario an error is raised
        """
        if self.teflo_options:
            res_label_list = list()
            user_labels = list()
            # labels present in all res
            res_label_list.extend(
                [lab for sc in self.scenario_graph for res in sc.get_all_resources() for lab in getattr(res, 'labels')])
            # labels provided by user at cli
            user_labels.extend([lab for lab in
                                self.teflo_options.get('labels', []) or self.teflo_options.get('skip_labels', [])])
            for label in user_labels:
                if label in res_label_list:
                    continue
                else:
                    raise TefloError("No resources were found corresponding to the label/skip_label %s."
                                      " Please check the labels provided during the run match the ones in "
                                      "scenario descriptor file" % label)
        return

    def run_all_validate_helper(self, final_passed_tasks, final_failed_tasks, status):
        """
        This is a helper method for running validate task for the whole scenario graph
        """
        do_validate = True
        self.logger.info(termcolor.colored("Validating against all scenarios!", "green"))
        self.logger.info("." * 50)
        sc: Scenario
        for sc in self.scenario_graph:
            if do_validate:
                self.logger.info("." * 50)
                self.logger.info(termcolor.colored('\'%s\' is validated from the scenario file: %s' %
                                                    (sc.name, sc.path), "green"))
                self.logger.info("." * 50)
                self.run_helper(sc=sc, tasklist=["validate"])
            if getattr(sc, "overall_status", None) is not None:
                if getattr(sc, "overall_status") == 1:
                    do_validate = False
        self.collect_final_passed_failed_tasks_status(final_passed_tasks, final_failed_tasks, status)

    def run_all_helper(self, tasklist: list, final_passed_tasks: list, final_failed_tasks: list, status: list):
        """
        This is a helper method for running all tasks for the whole scenario graph
        it will update final_passed_tasks, final_failed_tasks and status after it
        finish the run
        """

        with ExitStack() as stack:

            tasklist_run: list = deepcopy(tasklist)
            if "validate" in tasklist:
                tasklist_run.remove("validate")
                self.run_all_validate_helper(final_passed_tasks, final_failed_tasks, status)
                if status[0] == 1:
                    return
            if "cleanup" in tasklist:
                tasklist_run.remove("cleanup")
                stack.callback(partial(self.cleanup_helper, final_passed_tasks, final_failed_tasks, status))

            sc: Scenario
            for sc in self.scenario_graph:
                try:
                    self.run_helper(sc=sc, tasklist=tasklist_run)
                except TefloScenarioFailure as ex:
                    self.scenario_graph.reinit()
                    self.logger.error(ex)
                    break
            self.collect_final_passed_failed_tasks_status(final_passed_tasks, final_failed_tasks, status)

    def run(self, tasklist: list = TASKLIST):
        """
        This function assumes there are zero or more tasks to be
        loaded within the list of pipelines: ~self.pipelines.

        It will run through all resources within the ~self.scenario
        object (lists of hosts, actions, executes, reports), including
        tasks associated with the ~self.scenario itself, and find if any
        of them has a task to be loaded in the pipelines.

        Once a task is found, it is loaded within its respective
        pipeline and then each pipeline is sent to blaster blastoff.
        For every pipeline within ~self.pipelines,
        """

        # initialize the final passed task and failed task
        final_passed_tasks = []
        final_failed_tasks = []
        # initialize overall status
        status = [0]

        # save start time
        self.start()

        self._print_header(tasklist)

        self.run_all_helper(tasklist, final_passed_tasks, final_failed_tasks, status)

        for task in final_failed_tasks:
            if task in final_passed_tasks:
                final_passed_tasks.remove(task)

        self.end()
        # determine state
        # 0 is false here
        state = 'FAILED' if status[0] else 'PASSED'

        self._write_out_results()

        self._print_footer(final_passed_tasks, final_failed_tasks, state)

        self._archive_results()

        if self.config["CLEAN_CACHED_WORKSPACE_AFTER_EACH_RUN"].lower() == "true":
            self.clean_cached_remote_workspace()

        sys.exit(status[0])

    def clean_cached_remote_workspace(self):
        if os.path.isdir(self.config["REMOTE_WORKSPACE_DOWNLOAD_LOCATION"]):
            shutil.rmtree(self.config["REMOTE_WORKSPACE_DOWNLOAD_LOCATION"])

    def cleanup_helper(self, final_passed_tasks: list, final_failed_tasks: list, status: list):
        """
        This is a helper method for cleanup. It does cleanup for all scenarios in
        the scenario graph. It does cleanup in a reverse order to the provisoin/
        orchestarte/execute/report
        """

        cleanup_sc = []
        for sc in self.scenario_graph:
            cleanup_sc.append(sc)
        cleanup_sc.reverse()
        sc: Scenario
        for sc in cleanup_sc:
            try:
                self.logger.info("." * 50)
                self.logger.info(termcolor.colored('\'%s\' is running from the scenario file: %s' %
                                                   (sc.name, sc.path), "green"))
                self.logger.info("." * 50)
                self.run_helper(sc=sc, tasklist=["cleanup"])
            except TefloScenarioFailure as ex:
                self.scenario_graph.reinit()
                self.logger.error(ex)
                break

        self.collect_final_passed_failed_tasks_status(final_passed_tasks, final_failed_tasks, status)

    def collect_final_passed_failed_tasks_status(self, final_passed_tasks: list,
                                                 final_failed_tasks: list, status: list):
        """
        This method collects all failed and passed tasks from all scenarios in
        the self.scenario_graph
        """

        for sc in self.scenario_graph:

            if getattr(sc, "failed_tasks", None) is not None:
                for task in sc.failed_tasks:
                    if task not in final_failed_tasks:
                        final_failed_tasks.append(task)
                    if task in final_passed_tasks:
                        final_passed_tasks.remove(task)

            if getattr(sc, "passed_tasks", None) is not None:
                for task in sc.passed_tasks:
                    if task not in final_passed_tasks and task not in final_failed_tasks:
                        final_passed_tasks.append(task)

            if getattr(sc, "overall_status", None) is not None:
                if sc.overall_status == 1:
                    status[0] = 1

    def run_helper(self, sc: Scenario = None, tasklist: list = TASKLIST):
        """
        This is a helper method for running all tasks for a certain scenario
        """
        passed_tasks = list()
        failed_tasks = list()
        if len(tasklist) != 0:
            self.logger.info("." * 50)
            self.logger.info(termcolor.colored('\'%s\' is running from the scenario file: %s' %
                                               (sc.name, sc.path), "green"))
            self.logger.info("." * 50)
        # initialize overall status
        status = 0
        if not self.teflo_options.get('no_notify', False):
            self.notify('on_start', status, passed_tasks, failed_tasks, scenario=sc)

        try:
            for task in sort_tasklist(tasklist):
                self.logger.info(' * Task    : %s' % task)

                # initially update list of passed tasks
                passed_tasks.append(task)
                # TODO: MAKE THIS ONE TIME RUN

                data = self._run_pipeline(task, sc)
                self.scenario_graph.remove_resources_from_scenario(sc)

                # reload resource objects
                sc: Scenario
                # for sc in self.scenario_graph:
                sc.reload_resources(data)
                self.scenario_graph.reload_resources_from_scenario(sc)
                # Creating inventory only when task is provision
                if task == 'provision':
                    all_hosts = sc.get_assets()

                    for host in all_hosts:
                        if hasattr(host, 'groups') or hasattr(host, 'ip_address'):
                            self.logger.info('Populating inventory file with host(s) %s'
                                                % getattr(host, 'name'))
                    try:
                        self.cbn_inventory.create_inventory(all_hosts=all_hosts)

                    except Exception as ex:
                        raise TefloError("Error while creating the inventory for scenario %s: %s" % (sc.path, ex))

                self.logger.info("." * 50)
        except Exception as ex:
            # set overall status
            status = 1

            # pop task from passed list since it failed
            passed_tasks.pop(-1)

            # update list of failed tasks
            failed_tasks.append(task)

            self.logger.error(ex)

            self.scenario_graph.remove_resources_from_scenario(sc)
            # reload resource objects
            sc.reload_resources(ex.results)
            self.scenario_graph.reload_resources_from_scenario(sc)
            # roll back by cleaning up any resources that might have been provisioned
            if "cleanup" in tasklist and [item for item in failed_tasks if item != 'cleanup']:
                if [item for item in passed_tasks if item == 'provision'] \
                        or [item for item in failed_tasks if item == 'provision']:
                    self.logger.info("\n\n")
                    self.logger.warning("A failure occurred before running the cleanup task. "
                                        "Attempting to run the cleanup task to roll back all provisioned resources.")

                    try:
                        data = self._run_pipeline("cleanup", sc)
                        self.scenario_graph.remove_resources_from_scenario(sc)

                        # reload resource objects
                        sc.reload_resources(data)
                        passed_tasks.append(task)
                    except Exception as ex:
                        self.logger.error(ex)
                        self.logger.error("There was a problem running the cleanup task to roll back the "
                                          "resources. You may need to manually cleanup any provisioned resources")
                        failed_tasks.append(task)
                        raise TefloScenarioFailure("`%s` failed during running cleanup rollback" % sc.name)
        finally:
            setattr(sc, 'overall_status', status)
            setattr(sc, 'passed_tasks', passed_tasks)
            setattr(sc, 'failed_tasks', failed_tasks)
            self.scenario_graph.reload_resources_from_scenario(sc)
            if not self.teflo_options.get('no_notify', False):
                self.notify('on_complete', status, passed_tasks, failed_tasks, sc)

            def exit_on_status():

                state = 'FAILED' if status else 'PASSED'

                if str(self.config.get("SKIP_FAIL")).lower() != 'true' and \
                        str(self.config.get("SKIP_FAIL")).lower() != 'false' and \
                        self.config.get("SKIP_FAIL") is not None:
                    self.logger.error('The skip_fail variable can be true or false only. Running'
                                      ' as default value which is False')
                    self.config["SKIP_FAIL"] = 'False'

                if str(self.config.get("SKIP_FAIL")).lower() != 'true' \
                        and self._teflo_options.get('skip_fail') is not True and state is 'FAILED':
                    raise TefloScenarioFailure(
                        "Scenario `%s` failed during the Teflo run" % sc.name)

            exit_on_status()

    def notify(self, task, status=0, passed_tasks=None, failed_tasks=None, scenario: Scenario = None):
        """
        This method handle all notifications
        """

        self.logger.info('Sending out any notifications that are registered.')

        if task == 'on_demand':
            self.start()
            self._print_header(['notify'])
            self.logger.info(' * Task    : notify')
            sc: Scenario
            for sc in self.scenario_graph:
                try:
                    data = self._run_pipeline(task, sc)
                    self.scenario_graph.remove_resources_from_scenario(sc)
                    sc.reload_resources(data)
                    self.scenario_graph.reload_resources_from_scenario(sc)
                except Exception as ex:
                    status = 1
                    self.logger.error(ex)
                    self.logger.error(termcolor.colored(
                        'One or more notifications failed. Refer to the scenario.log', "red"))
                    self.scenario_graph.remove_resources_from_scenario(sc)
                    sc.reload_resources(ex.results)
                    self.scenario_graph.reload_resources_from_scenario(sc)
                    # save end time
            self.end()
            # determine state
            state = 'FAILED' if status else 'PASSED'

            self._write_out_results()
            final_passed_tasks = []
            final_failed_tasks = []
            self.collect_final_passed_failed_tasks_status(final_passed_tasks, final_failed_tasks, [status])

            self._print_footer(final_passed_tasks, final_failed_tasks, state)

            self._archive_results()
            sys.exit(status)
        else:
            setattr(scenario, 'overall_status', status)

            if passed_tasks:
                setattr(scenario, 'passed_tasks', passed_tasks)

            if failed_tasks:
                setattr(scenario, 'failed_tasks', failed_tasks)

            # blast off the pipeline list of tasks
            try:
                data = self._run_pipeline(task, scenario)
                self.scenario_graph.remove_resources_from_scenario(scenario)
                scenario.reload_resources(data)
                self.scenario_graph.reload_resources_from_scenario(scenario)
            except Exception as ex:
                status = 1
                self.logger.error(ex)
                self.logger.error('One or more notifications failed. Refer to the scenario.log')
                self.scenario_graph.remove_resources_from_scenario(scenario)
                scenario.reload_resources(ex.results)
                self.scenario_graph.reload_resources_from_scenario(scenario)

    @property
    def root_scenario_filename(self):
        return self.scenario_graph.root.path

    @property
    def root_scenario_fullpath(self):
        return self.scenario_graph.root.fullpath

    def _run_pipeline(self, task, scenario: Scenario):
        data = {}

        # create a pipeline builder object
        pipe_builder = PipelineFactory.get_pipeline(task)

        # check if teflo supports the task
        if not pipe_builder.is_task_valid():
            self.logger.warning('Task %s is not valid by teflo.', task)
            return data

        pipeline = pipe_builder.build(scenario, self.teflo_options, scenario_graph=self.scenario_graph)
        self.logger.info('.' * 50)
        self.logger.info('Starting tasks on pipeline: %s',
                         pipeline.name)
        # check if pipeline has tasks to be run
        if not pipeline.tasks:
            self.logger.warning('... no tasks to be executed ...')
            return data

        # create blaster object with pipeline to run
        blast = blaster.Blaster(pipeline.tasks)
        # blast off the pipeline list of tasks reload_resources
        data = blast.blastoff(
            serial=not pipeline.type.__concurrent__,
            raise_on_failure=True
        )

        return data

    @property
    def data_folder_results_yml_path(self):
        return os.path.join(self.data_folder, RESULTS_FILE)

    @property
    def final_results_yml_path(self):
        return os.path.join(self.config["RESULTS_FOLDER"], RESULTS_FILE)

    def _data_folder_resultsyml_exist(self):
        return os.path.exists(self.data_folder_results_yml_path)

    def _final_results_yml_exists(self):
        return os.path.exists(self.final_results_yml_path)

    def _create_final_result_yml(self):
        """
        This method create the final result
        scenario file and put it to data folder
        """

        if self._data_folder_resultsyml_exist():
            return
        if preproc_path(self.config["RESULTS_FOLDER"]) in self.root_scenario_fullpath or \
            preproc_path(self.data_folder) in self.root_scenario_fullpath or \
                self.root_scenario_filename == "results.yml":
            root_scenario_results_path = os.path.join(self.data_folder, self.root_scenario_filename)
        else:
            root_scenario_results_path = os.path.join(
                self.data_folder, self.root_scenario_filename.split(".")[0] + "_results.yml")
        if root_scenario_results_path != self.final_results_yml_path and self.root_scenario_filename != "results.yml":
            if self._final_results_yml_exists():
                os.remove(self.final_results_yml_path)
        os.system("cp %s %s" % (root_scenario_results_path, self.data_folder_results_yml_path))

    def _print_header(self, tasklist):

        self.logger.info('\n')
        self.logger.info('TEFLO RUN (START)'.center(79))
        self.logger.info('-' * 79)
        self.logger.info(' * Data Folder           : %s' % self.data_folder)
        self.logger.info(' * Workspace             : %s' % self.workspace)
        self.logger.info(' * Log Level             : %s' % self.config['LOG_LEVEL'])
        self.logger.info(' * Tasks                 : %s' % tasklist)
        self.logger.info(' * Iterate Method        : %s' % self.scenario_graph.iterate_method)
        for sc in self.scenario_graph:
            self.logger.info(' * Scenario              : %s' % getattr(sc, 'name'))
        self.logger.info('-' * 79 + '\n')

    def _write_out_results(self):
        """
        write all results to sc.path_results.yml
        if you are running sdf under data folder
        or results folder, it will not generate
        new sc.path_results.yml
        """
        sc: Scenario
        for sc in self.scenario_graph:
            # use filename because the scenario name could
            # contain some special characters, which is not good for
            # file generation
            if preproc_path(self.config["RESULTS_FOLDER"]) in sc.fullpath or \
                preproc_path(self.data_folder) in sc.fullpath \
                    or sc.path == "results.yml":
                ch_result_abs_name = os.path.join(self.data_folder, sc.path)
            else:
                ch_result_abs_name = os.path.join(self.data_folder, sc.path.split(".")[0] + '_results.yml')
            file_mgmt('w', ch_result_abs_name, sc.profile())
            # Adding child_result_list with results file in the RESULTS_FOLDER instead of absolute path
        self._create_final_result_yml()

    def _print_footer(self, passed_tasks, failed_tasks, state):

        self.logger.info('\n')
        self.logger.info('SCENARIO RUN (END)'.center(79))
        self.logger.info('-' * 79)
        self.logger.info(' * Duration                       : %dh:%dm:%ds' %
                         (self.hours, self.minutes, self.seconds))
        if passed_tasks.__len__() > 0:
            self.logger.info(' * Passed Tasks                   : %s' %
                             passed_tasks)
        if failed_tasks.__len__() > 0:
            self.logger.info(' * Failed Tasks                   : %s' %
                             failed_tasks)
        self.logger.info(' * Results Folder                 : %s' %
                         self.config['RESULTS_FOLDER'])
        self.logger.info(' * Iterate Method                 : %s' %
                         self.scenario_graph.iterate_method)
        for sc in self.scenario_graph:
            self.logger.info(' * Scenario Definition            : %s' % sc.name)
        self.logger.info(' * Final Scenario Definition      : %s' % self.final_results_yml_path)
        self.logger.info('-' * 79)
        self.logger.info('TEFLO RUN (RESULT=%s)' % state)

    def _archive_results(self):
        """
        This method copy all files under
        data folder to results folder
        """

        # archive everything from the data folder into the results folder
        os.system('cp -r %s/* %s' % (self.data_folder, self.config['RESULTS_FOLDER']))

        # also archive the inventory file if a static inventory directory differnt thant default inventory dir
        # is specified
        if self.static_inv_dir:
            if os.listdir(self.config['INVENTORY_FOLDER']):
                inv_results_dir = os.path.join(self.config['RESULTS_FOLDER'], 'inventory')
                if not os.path.samefile(self.config['INVENTORY_FOLDER'], inv_results_dir):
                    os.system('cp -r %s/* %s' % (self.config['INVENTORY_FOLDER'], inv_results_dir))

    def create_teflo_workspace(self, ctx, dirname):
        """Clones the teflo examples git repo and copy the workspace files."""

        # Download the teflo examples repo to cache folder
        url = 'https://github.com/redhatqe/teflo_examples.git'
        cmd = 'git clone ' + url + ' .teflo_cache'
        result = exec_local_cmd(cmd)

        if result[0] != 0:
            click.echo("A problem occurred while cloning the teflo_examples project")
            ctx.exit()

        # Copy the files to the new directory and clean cache
        copy_tree('./.teflo_cache/teflo_init/', dirname)
        shutil.rmtree('.teflo_cache')

    def showgraph(self, ctx, scenario_graph: ScenarioGraph):
        """Show scenario graph includes structure"""
        from termcolor import colored
        click.echo(colored("Below is the structure of the Scenario Definition Files", "green"))
        print('\n')
        print('ITERATE METHOD:', scenario_graph.iterate_method)
        print('\n\n\n')
        print(colored(scenario_graph, "green"))
