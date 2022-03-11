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
    Teflo's ansible executor plugin which contains all the necessary
    methods to process steps in the executes block defined within the scenario descriptor
    file. This pluging uses ansible to process these steps

    :copyright: (c) 2021 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""

import ast
import os.path
import os
import textwrap
from teflo.core import ExecutorPlugin
from teflo.exceptions import ArchiveArtifactsError, TefloExecuteError, AnsibleServiceError
from teflo.helpers import DataInjector, get_ans_verbosity, create_testrun_results, schema_validator
from teflo.ansible_helpers import AnsibleService


class AnsibleExecutorPlugin(ExecutorPlugin):
    """ The main executor for Teflo.

    The AnsibleExecutorPlugin class provides three different types on how you can execute
    tests. Its intention is to be generic enough where you just need to supply
    your test commands and it will process them. All tests executed against
    remote hosts will be run through ansible.
    """

    # keeping the name as runner for backward compatibility
    __executor_name__ = 'runner'
    __schema_file_path__ = os.path.abspath(os.path.join(os.path.dirname(__file__), "files/schema.yml"))
    __schema_ext_path__ = os.path.abspath(os.path.join(os.path.dirname(__file__), "files/extensions.py"))

    def __init__(self, package):
        """Constructor.

        :param package: execute resource
        :type package: object
        """
        super(AnsibleExecutorPlugin, self).__init__(package)

        # set required attributes
        self._desc = getattr(package, 'description')
        self.all_hosts = getattr(package, 'all_hosts', [])
        self.playbook = getattr(package, 'playbook', None)
        self.script = getattr(package, 'script', None)
        self.shell = getattr(package, 'shell', None)
        self.git = getattr(package, 'git', None)
        self.artifacts = getattr(package, 'artifacts')
        self.options = getattr(package, 'ansible_options', None)
        self.ignorerc = getattr(package, 'ignore_rc', False)
        self.validrc = getattr(package, 'valid_rc', None)
        self.env_var = getattr(package, 'environment_vars', {})
        self.injector = DataInjector(self.all_hosts)

        self.ans_service = AnsibleService(self.config, self.hosts, self.all_hosts, self.options,
                                          concurrency=self.config['TASK_CONCURRENCY']['EXECUTE'].lower(),
                                          env_var=self.env_var)

        self.ans_verbosity = get_ans_verbosity(self.config)

        # attribute defining overall status of test execution. why is this
        # needed? when a test fails we handle the exception raised and call
        # the method to archive test artifacts. once fetching artifacts is
        # finished this status is used to fail teflo (if needed)
        self.status = 0

    def validate(self):
        """Validate."""
        # schema validation for ansible_orchestrate schema
        schema_validator(schema_data=self.build_profile(self.execute), schema_files=[self.__schema_file_path__],
                         schema_ext_files=[self.__schema_ext_path__])

    def __git__(self):

        self.status = self.ans_service.run_git_playbook(self.git)
        if self.status != 0:
            raise TefloExecuteError('Failed to clone git repositories!')

    def __shell__(self):
        self.logger.info('Executing shell commands:')
        for index, shell in enumerate(self.shell):

            result = self.ans_service.run_shell_playbook(shell)

            ignorerc = self.ignorerc
            validrc = self.validrc

            if "ignore_rc" in shell and shell['ignore_rc']:
                ignorerc = shell['ignore_rc']
            elif "valid_rc" in shell and shell['valid_rc']:
                validrc = shell['valid_rc']

            if ignorerc:
                self.logger.info("Ignoring the rc for: %s" % shell['command'])

            elif validrc:
                if result['rc'] not in validrc:
                    self.status = 1
                    self.logger.error('Command %s failed. Host=%s rc=%d\nError: Please look at the'
                                      ' scenario log for failure.'
                                      % (shell['command'], result['host'], result['rc']))
                    self.logger.debug("During the failure these messages were thrown as a part of"
                                      " stderr:\n %s" % result['err'])

            else:
                if result['rc'] != 0:
                    self.status = 1
                    self.logger.error('Command %s failed. Host=%s rc=%d\nError: Please look at the'
                                      ' scenario log for failure.'
                                      % (shell['command'], result['host'], result['rc']))
                    self.logger.debug("During the failure these messages were thrown as a part of"
                                      " stderr:\n %s" % result['err'])

            if self.status == 1:
                raise ArchiveArtifactsError('Command %s failed to run ' % shell['name'])
            else:
                self.logger.info('Successfully executed command : %s' % shell['command'])

    def __script__(self):
        self.logger.info('Executing scripts:')
        for index, script in enumerate(self.script):

            result = self.ans_service.run_script_playbook(script)

            ignorerc = self.ignorerc
            validrc = self.validrc

            if "ignore_rc" in script and script['ignore_rc']:
                ignorerc = script['ignore_rc']
            elif "valid_rc" in script and script['valid_rc']:
                validrc = script['valid_rc']

            if ignorerc:
                self.logger.info("Ignoring the rc for: %s" % script['name'])

            elif validrc:

                if result['rc'] not in validrc:
                    self.status = 1
                    self.logger.error('Script %s failed. Host=%s rc=%d\nError: Please look at the'
                                      ' scenario log for failure.'
                                      % (script['name'], result['host'], result['rc']))
                    self.logger.debug("During the failure these messages were thrown as a part of"
                                      " stderr:\n %s" % result['err'])
            else:
                if result['rc'] != 0:
                    self.status = 1
                    self.logger.error('Script %s failed. Host=%s rc=%d\nError: Please look at the'
                                      ' scenario log for failure.'
                                      % (script['name'], result['host'], result['rc']))
                    self.logger.debug("During the failure these messages were thrown as a part of"
                                      " stderr:\n %s" % result['err'])
            if self.status == 1:
                raise ArchiveArtifactsError('Script %s failed to run' % script['name'])
            else:
                self.logger.info('Successfully executed script : %s' % script['name'])

    def __playbook__(self):
        self.logger.info('Executing playbooks:')
        for index, playbook in enumerate(self.playbook):

            results = self.ans_service.run_playbook(playbook)

            ignorerc = self.ignorerc
            if "ignore_rc" in playbook and playbook['ignore_rc']:
                ignorerc = playbook['ignore_rc']

            if ignorerc:
                self.logger.info("Ignoring the rc for: %s"
                                 % playbook['name'])
            elif results[0] != 0:
                self.status = 1
                if results[1]:
                    self.logger.debug("During the failure these messages were thrown as a part of"
                                      " stderr:\n %s " % results[1])
                raise ArchiveArtifactsError('Playbook %s failed to run.\nPlease look at the scenario'
                                            ' log for ansible failure.' % playbook['name'])
            else:
                self.logger.info('Successfully executed playbook : %s' % playbook['name'])

    def __artifacts__(self):
        """Archive artifacts produced by the tests.

        This method takes a string formatted playbook, writes it to disk,
        provides the test artifacts details to the playbook and runs it. The
        result is on the machine where teflo is run, all test artifacts will
        be archived inside the data folder.

        Example artifacts archive structure:

        artifacts/
            host_01/
                test_01_output.log
                results/
                    ..
            host_02/
                test_01_output.log
                results/
                    ..
        """
        # local path on disk to save artifacts
        destination = self.config['ARTIFACT_FOLDER']

        self.logger.info('Fetching test artifacts @ %s' % destination)

        artifact_location = list()

        # settings required by synchronize module
        os.environ['ANSIBLE_LOCAL_TEMP'] = '$HOME/.ansible/tmp'
        os.environ['ANSIBLE_REMOTE_TEMP'] = '$HOME/.ansible/tmp'

        # setting variable so to no display any skipped tasks
        os.environ['DISPLAY_SKIPPED_HOSTS'] = 'False'

        results = self.ans_service.run_artifact_playbook(destination, self.artifacts)

        if results[0] != 0:
            self.logger.error(results[1])
            raise TefloExecuteError('A failure occurred while trying to copy '
                                     'test artifacts.')

        # Get results from file
        try:
            with open('sync-results-' + self.ans_service.uid + '.txt') as fp:
                lines = fp.read().splitlines()
        except (IOError, OSError) as ex:
            self.logger.error(ex)
            raise TefloExecuteError('Failed to find the sync-results.txt file '
                                     'which means there was an uncaught failure running '
                                     'the synchronization playbook. Please enable verbose Ansible '
                                     'logging in the teflo.cfg file and try again.')

        # Build Results
        sync_results = []
        for line in lines:
            host, artifact, dest, skipped, rc = ast.literal_eval(textwrap.dedent(line).strip())
            sync_results.append({'host': host, 'artifact': artifact, 'destination': dest, 'skipped': skipped, 'rc': rc})

        # remove Sync Results file
        os.remove('sync-results-' + self.ans_service.uid + '.txt')

        for r in sync_results:
            if r['rc'] != 0 and not r['skipped']:
                # checking if exit on error is set to true in teflo.cfg file
                if self.config.get('RUNNER_EXIT_ON_ERROR', 'False').lower() == 'true':
                    raise TefloExecuteError('Failed to copy the artifact(s), %s, from %s' % (r['artifact'], r['host']))
                else:
                    self.logger.error('Failed to copy the artifact(s), %s, from %s' % (r['artifact'], r['host']))
            if r['rc'] == 0 and not r['skipped']:
                temp_list = r['artifact'].replace('[', '').replace(']', '').replace("'", "").split(',')
                res_folder_parts = self.config['RESULTS_FOLDER'].split('/')
                dest_path_parts = r['destination'].split('/')

                if not self.ans_service.ans_extra_vars['localhost']:
                    art_list = [a[11:] for a in temp_list if 'cd+' not in a]
                    path = '/'.join(r['destination'].split('/')[-3:])
                else:
                    path = '/'.join(r['destination'].split('/')[len(res_folder_parts):-1])
                    art_list = ['/'.join(a.replace('’', "").split('->')[-1].split('/')[(len(dest_path_parts) - 1):])
                                for a in temp_list]
                self.logger.info('Copied the artifact(s), %s, from %s' % (art_list, r['host']))

                # Adding the only the artifacts which are not already present
                for artifact in art_list:
                    art = os.path.join(path, artifact)
                    if art not in artifact_location:
                        artifact_location.append(art)
            if r['skipped']:
                self.logger.warning('Could not find artifact(s), %s, on %s. Make sure the file exists '
                                    'and defined properly in the definition file.' % (r['artifact'], r['host']))
        # Update the execute resource with the location of artifacts
        if self.execute.artifact_locations:
            for item in artifact_location:
                if item not in self.execute.artifact_locations:
                    self.execute.artifact_locations.append(item)
        else:
            self.execute.artifact_locations = artifact_location

        if self.config.get('RUNNER_TESTRUN_RESULTS') and self.config.get('RUNNER_TESTRUN_RESULTS').lower() == 'false':
            self.execute.testrun_results = {}
        else:
            self.execute.testrun_results = create_testrun_results(self.injector.inject_list
                                                                  (self.execute.artifact_locations), self.config)
        # printing out the testrun results on the console
        self._print_testrun_results()

    def _print_testrun_results(self):
        """
        This method prints out the aggregate and individual test results for the xml files in the artifacts collected
        """

        if self.execute.testrun_results and self.execute.testrun_results.get('individual_results'):
            self.logger.info('\n')
            self.logger.info('-' * 79)
            self.logger.info('TESTRUN RESULTS SUMMARY'.center(79))
            self.logger.info('-' * 79)
            self.logger.info(' * AGGREGATE RESULTS * '.center(79))
            self.logger.info('-' * 79)
            self.logger.info(' * Total Tests             : %s' %
                             self.execute.testrun_results['aggregate_testrun_results']['total_tests'])
            self.logger.info(' * Failed Tests            : %s' %
                             self.execute.testrun_results['aggregate_testrun_results']['failed_tests'])
            self.logger.info(' * Error Tests             : %s' %
                             self.execute.testrun_results['aggregate_testrun_results']['error_tests'])
            self.logger.info(' * Skipped Tests           : %s' %
                             self.execute.testrun_results['aggregate_testrun_results']['skipped_tests'])
            self.logger.info(' * Passed Tests            : %s' %
                             self.execute.testrun_results['aggregate_testrun_results']['passed_tests'])
            self.logger.info('-' * 79)
            if len(self.execute.testrun_results.get('individual_results')) > 1:
                self.logger.info(' * INDIVIDUAL RESULTS * '.center(79))
                self.logger.info('-' * 79)
                for res in self.execute.testrun_results.get('individual_results'):
                    for keys, values in res.items():
                        self.logger.info(' * File Name               : %s' % keys)
                        self.logger.info(' * Total Tests             : %s' % values['total_tests'])
                        self.logger.info(' * Failed Tests            : %s' % values['failed_tests'])
                        self.logger.info(' * Error Tests             : %s' % values['error_tests'])
                        self.logger.info(' * Skipped Tests           : %s' % values['skipped_tests'])
                        self.logger.info(' * Passed Tests            : %s' % values['passed_tests'])
                        self.logger.info('-' * 79)
        else:
            self.logger.info(' No artifacts were collected OR artifacts collected had no xml files')
            self.logger.info('-' * 79 + '\n')

    def run(self):
        """Run.

        The run method is the main entry point for the runner executor. This
        method will invoke various other methods in order to successfully
        run the runners execute types given.
        """
        for attr in ['git', 'shell', 'playbook', 'script', 'artifacts']:
            # skip if the execute resource does not have the attribute defined
            if not getattr(self, attr):
                continue

            # call the method associated to the execute resource attribute
            try:
                getattr(self, '__%s__' % attr)()
            except (ArchiveArtifactsError, TefloExecuteError, AnsibleServiceError) as ex:
                # test execution failed, test artifacts may still have been
                # generated. lets go ahead and archive these for debugging
                # purposes
                self.logger.error(ex.message)
                if (attr != 'git' or attr != 'artifacts') and self.artifacts is not None:
                    self.logger.info('Test Execution has failed but still fetching any test generated artifacts')
                    self.__artifacts__()
                    self.status = 1

                if self.status:
                    break
            finally:
                self.ans_service.alog_update(folder_name='ansible_executor')
        return self.status
