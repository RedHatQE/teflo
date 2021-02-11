# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 Red Hat, Inc.
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

    :copyright: (c) 2020 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""
import errno
import os
import sys

import blaster
import yaml
from glob import glob
from . import __name__ as __teflo_name__
from .constants import TASKLIST, RESULTS_FILE, DATA_FOLDER, DEFAULT_INVENTORY, DEFAULT_ARTIFACT
from .core import TefloError, LoggerMixin, TimeMixin, Inventory
from .helpers import file_mgmt, gen_random_str, sort_tasklist
from .resources import Scenario, Asset, Action, Report, Execute, Notification
from .utils.config import Config
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
        self.cbn_inventory = Inventory.get_instance(self.config, self._uid)

        self.scenario = Scenario(config=self.config)

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

    def _populate_scenario_resources(self, scenario_obj, scenario_stream):

        scenario_data = yaml.safe_load(scenario_stream)
        pro_items = scenario_data.pop('provision', None)
        orc_items = scenario_data.pop('orchestrate', None)
        exe_items = scenario_data.pop('execute', None)
        rpt_items = scenario_data.pop('report', None)
        inc_items = scenario_data.pop('include', None)
        notify_items = scenario_data.pop('notifications', None)

        scenario_obj.load(scenario_data)

        scenario_obj.load_resources(Asset, pro_items)
        scenario_obj.load_resources(Action, orc_items)
        scenario_obj.load_resources(Execute, exe_items)
        scenario_obj.load_resources(Report, rpt_items)
        scenario_obj.load_resources(Notification, notify_items)

    def load_from_yaml(self, filedata):
        """
        Given the YAML filename with the scenario description, this
        function will load all resources described in the file with
        the teflo object.

        The main sections of the YAML descriptor (provision, orchestrate,
        execute and report) will be taken of the data in its respective
        data object. All the rest of the attributes within the YAML file
        will be loaded into the ~self.scenario object.

        If include section for included scenarios is present then they get
        added as child scenario objects for the main scenario(~self.scenario).
        These scenarios in turn go through the same process of taking out the
        main sections from the data in its respective data object

        The additional attributes within the file will be ignored by the Scenario
        resource.

        Once each data section is taken of the main descriptor, it will
        then be be loaded in each respective lists within the
        ~self.scenario object.

        :param filedata: list of full data object for the YAML file descriptor
        :return:
        """
        # setting up master scenario
        self.scenario.yaml_data = filedata[0]
        self._populate_scenario_resources(self.scenario, filedata[0])

        # creating child scenario objects
        if len(filedata) > 1:
            for scenario_stream in filedata[1:]:
                ch_scenario = Scenario(config=self.config)
                ch_scenario.yaml_data = scenario_stream
                self._populate_scenario_resources(ch_scenario, scenario_stream)
                self.scenario.add_child_scenario(ch_scenario)

        self._validate_labels()

    def list_labels(self):
        """This method displays all the labels in the scenario"""
        res_label_dict = dict()
        # getting all labels from all resources in the scenario
        for res in self.scenario.get_all_resources():
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
            res_label_list.extend([lab for res in self.scenario.get_all_resources() for lab in getattr(res, 'labels')])
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

    def run(self, tasklist=TASKLIST):
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
        # lists to control which tasks passed or failed
        passed_tasks = list()
        failed_tasks = list()

        # initialize overall status
        status = 0

        # save start time
        self.start()

        self._print_header(tasklist)

        try:
            for task in sort_tasklist(tasklist):
                self.logger.info(' * Task    : %s' % task)

                # initially update list of passed tasks
                passed_tasks.append(task)
                if not self.teflo_options.get('no_notify', False):
                    self.notify('on_start', status, passed_tasks, failed_tasks)
                data = self._run_pipeline(task)

                # reload resource objects
                self.scenario.reload_resources(data)

                if self.scenario.child_scenarios:
                    [sc.reload_resources(data) for sc in self.scenario.child_scenarios]

                # Creating inventory only when task is provision
                if task == 'provision':
                    try:
                        # create the master inventory
                        for host in self.scenario.get_all_assets():
                            if (hasattr(host, 'role') or hasattr(host, 'groups')) and hasattr(host, 'ip_address'):
                                self.logger.info('Populating master inventory file with host(s) %s'
                                                 % getattr(host, 'name'))

                        self.cbn_inventory.create_master(all_hosts=self.scenario.get_all_assets())
                    except Exception as ex:
                        raise TefloError("Error while creating the master inventory %s" % ex)

                self.logger.info("." * 50)
        except Exception as ex:
            # set overall status
            status = 1

            # pop task from passed list since it failed
            passed_tasks.pop(-1)

            # update list of failed tasks
            failed_tasks.append(task)

            self.logger.error(ex)

            # reload resource objects
            self.scenario.reload_resources(ex.results)

            if self.scenario.child_scenarios:
                [sc.reload_resources(ex.results) for sc in self.scenario.child_scenarios]

            # roll back by cleaning up any resources that might have been provisioned
            if 'cleanup' in tasklist and [item for item in failed_tasks if item != 'cleanup']:
                if [item for item in passed_tasks if item == 'provision'] \
                        or [item for item in failed_tasks if item == 'provision']:
                    self.logger.info("\n\n")
                    self.logger.warning("A failure occurred before running the cleanup task. "
                                        "Attempting to run the cleanup task to roll back all provisioned resources.")
                    task = tasklist[tasklist.index('cleanup')]

                    try:

                        data = self._run_pipeline(task)

                        # reload resource objects
                        self.scenario.reload_resources(data)
                        if self.scenario.child_scenarios:
                            [sc.reload_resources(data) for sc in self.scenario.child_scenarios]
                        passed_tasks.append(task)
                    except Exception as ex:
                        self.logger.error(ex)
                        self.logger.error("There was a problem running the cleanup task to roll back the "
                                          "resources. You may need to manually cleanup any provisioned resources")
                        failed_tasks.append(task)
                        raise
        finally:
            # save end time
            self.end()
            # determine state
            state = 'FAILED' if status else 'PASSED'

            # finally send out any notifications
            if not self.teflo_options.get('no_notify', False):
                self.notify('on_complete', status, passed_tasks, failed_tasks)

            self._write_out_results()

            self._print_footer(passed_tasks, failed_tasks, state)

            self._archive_results()

            sys.exit(status)

    def notify(self, task, status=0, passed_tasks=None, failed_tasks=None):

        setattr(self.scenario, 'overall_status', status)
        setattr(self.scenario, 'passed_tasks', [])
        setattr(self.scenario, 'failed_tasks', [])

        if passed_tasks:
            setattr(self.scenario, 'passed_tasks', passed_tasks)

        if failed_tasks:
            setattr(self.scenario, 'failed_tasks', failed_tasks)

        if task == 'on_demand':
            self.start()
            self._print_header(['notify'])
            self.logger.info(' * Task    : notify')

        # blast off the pipeline list of tasks
        try:

            self.logger.info('Sending out any notifications that are registered.')
            data = self._run_pipeline(task)

            # reload resource objects
            self.scenario.reload_resources(data)

            if self.scenario.child_scenarios:
                [sc.reload_resources(data) for sc in self.scenario.child_scenarios]
        except Exception as ex:
            status = 1
            self.logger.error(ex)
            self.logger.error('One or more notifications failed. Refer to the scenario.log')

            # reload resource objects
            self.scenario.reload_resources(ex.results)

            if self.scenario.child_scenarios:
                [sc.reload_resources(ex.results) for sc in self.scenario.child_scenarios]
        finally:
            if task == 'on_demand':
                # save end time
                self.end()
                # determine state
                state = 'FAILED' if status else 'PASSED'

                self._write_out_results()

                self._print_footer(getattr(self.scenario, 'passed_tasks'),
                                   getattr(self.scenario, 'failed_tasks'),
                                   state)

                self._archive_results()

                sys.exit(status)

    def _run_pipeline(self, task):

        data = {}

        # create a pipeline builder object
        pipe_builder = PipelineFactory.get_pipeline(task)

        # check if teflo supports the task
        if not pipe_builder.is_task_valid():
            self.logger.warning('Task %s is not valid by teflo.', task)
            return data

        pipeline = pipe_builder.build(self.scenario, self.teflo_options)

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

    def _print_header(self, tasklist):

        self.logger.info('\n')
        self.logger.info('TEFLO RUN (START)'.center(79))
        self.logger.info('-' * 79)
        self.logger.info(' * Data Folder           : %s' % self.data_folder)
        self.logger.info(' * Workspace             : %s' % self.workspace)
        self.logger.info(' * Log Level             : %s' % self.config['LOG_LEVEL'])
        self.logger.info(' * Tasks                 : %s' % tasklist)
        self.logger.info(' * Scenario              : %s' % getattr(self.scenario, 'name'))
        if self.scenario.child_scenarios:
            self.logger.info(' * Included Scenario(s)  : %s' % [getattr(sc, 'name') for sc in
                                                                self.scenario.child_scenarios])
        self.logger.info('-' * 79 + '\n')

    def _write_out_results(self):

        # check if child scenario exist, update the new child_result and append to ch_result_list.
        if self.scenario.child_scenarios:
            child_result_list = []
            for sc in self.scenario.child_scenarios:
                ch_result_file_name = sc.name + '_results.yml'
                ch_result_abs_name = os.path.join(self.data_folder, sc.name + '_results.yml')
                file_mgmt('w', ch_result_abs_name, sc.profile())
                # Adding child_result_list with results file in the RESULTS_FOLDER instead of absolute path
                child_result_list.append(os.path.join(self.config['RESULTS_FOLDER'], ch_result_file_name))

            # Add the child_result_list to the included_scenario_names property
            self.scenario.__setattr__('included_scenario_names', child_result_list)

        # Write the main scenario results
        file_mgmt('w', self.results_file, self.scenario.profile())

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

        self.logger.info(' * Included Scenario Definition   : %s' % self.scenario.included_scenario_names)
        self.logger.info(' * Final Scenario Definition      : %s' % os.path.join(self.config['RESULTS_FOLDER'],
                                                                                 RESULTS_FILE))
        self.logger.info('-' * 79)
        self.logger.info('TEFLO RUN (RESULT=%s)' % state)

    def _archive_results(self):

        # archive everything from the data folder into the results folder
        os.system('cp -r %s/* %s' % (self.data_folder, self.config['RESULTS_FOLDER']))

        # also archive the inventory file if a static inventory directory differnt thant default inventory dir
        # is specified
        if self.static_inv_dir:
            if os.listdir(self.config['INVENTORY_FOLDER']):
                inv_results_dir = os.path.join(self.config['RESULTS_FOLDER'], 'inventory')
                os.system('cp -r %s/* %s' % (self.config['INVENTORY_FOLDER'], inv_results_dir))
