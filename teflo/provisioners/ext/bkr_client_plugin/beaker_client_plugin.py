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
    teflo.provisioners.beaker_client

    Teflo's own Beaker provisioner. This module handles everything from
    authentication to creating/deleting resources in Beaker.

    :copyright: (c) 2021 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""
from __future__ import unicode_literals
import socket
import time
from xml.dom.minidom import parse, parseString

import os
import paramiko
import stat

from teflo.core import ProvisionerPlugin
from teflo.exceptions import BeakerProvisionerError
from teflo.helpers import exec_local_cmd, schema_validator


class BeakerClientProvisionerPlugin(ProvisionerPlugin):
    """The main class for teflo Beaker client provisioner plugin.

    This provisioner will interact with the Beaker server using the
    beaker client (bkr) to submit jobs to get resources from Beaker.

    Warning:
        Clashing (potential loss of data) will occur when trying to perform
        multiple requests with different authentication in the same namespace
        (with same config file).
    """
    __plugin_name__ = "beaker-client"
    __schema_file_path__ = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                        "schema.yml"))

    def __init__(self, asset):
        """Constructor.

        :param asset: The asset object.
        :type asset: object
        """
        super(BeakerClientProvisionerPlugin, self).__init__(asset)

        self.job_xml = 'bkrjob_%s.xml' % getattr(self.asset, 'name')
        self.bkr_xml = BeakerXML()
        self.conf_dir = '%s/.beaker_client' % os.path.expanduser('~')
        self.conf = '%s/config' % self.conf_dir
        self.url = ''

        # configure beaker conf
        self._build_config()

    def _build_config(self):
        """Build beaker configuration for authentication.

        This method will build the configuration file based on the type of
        authentication method (username/password or kerberos).
        """
        # create conf directory
        if not os.path.isdir(self.conf_dir):
            os.makedirs(self.conf_dir)

        if 'hub_url' in self.provider_credentials and self.provider_credentials['hub_url']:
            self.url = self.provider_credentials['hub_url']

        if os.path.isfile(self.conf):
            self.logger.info('Beaker config already exists, skip creation.')
            return

        # open conf file for writing
        conf_obj = open(self.conf, 'w')

        conf_obj.write('HUB_URL = "%s"\n' % self.url)

        # write the path to beaker trusted ssl certs if specified.
        if 'ca_cert' in self.provider_credentials and self.provider_credentials['ca_cert']:
            self.logger.debug('ca_cert was provided %s' % self.provider_credentials['ca_cert'])
            conf_obj.write('CA_CERT = "%s"\n' % self.provider_credentials['ca_cert'])

        if 'username' in self.provider_credentials and self.provider_credentials['username'] \
                and 'password' in self.provider_credentials and self.provider_credentials['password']:
            self.logger.debug('Authentication by username/password.')

            conf_obj.write('AUTH_METHOD = "password"\n')
            conf_obj.write('USERNAME = "%s"\n' % self.provider_credentials['username'])
            conf_obj.write('PASSWORD = "%s"\n' % self.provider_credentials['password'])
        elif 'keytab' in self.provider_credentials and self.provider_credentials['keytab'] \
                and 'keytab_principal' in self.provider_credentials \
                and self.provider_credentials["keytab_principal"]:
            self.logger.debug('Authentication by keytab.')

            conf_obj.write('AUTH_METHOD = "krbv"\n')

            keytab = os.path.join(self.workspace, self.provider_credentials['keytab'])

            conf_obj.write('KRB_KEYTAB = "%s"\n' % keytab)
            conf_obj.write('KRB_PRINCIPAL = "%s"\n' % self.provider_credentials[
                'keytab_principal'])
            conf_obj.write('KRB_REALM = "REDHAT.COM"\n')
        conf_obj.close()

    def _connect(self):
        """Connect to beaker."""
        data = exec_local_cmd('bkr whoami')
        if data[0] != 0:
            self.logger.error(data[2])
            raise BeakerProvisionerError('Connection to beaker failed!')
        self.logger.info('Connected to beaker!')

    def authenticate(self):
        """Authenticate with beaker."""
        self._connect()

    def gen_bkr_xml(self):
        """Create beaker job xml based on host requirements.

        This method builds xml content and writes xml to file.
        """
        # set beaker xml absolute file path
        bkr_xml_file = os.path.join(self.data_folder, self.job_xml)

        # set attributes for beaker xml object
        for key, value in self.provider_params.items():
            if key != 'name':
                if value:
                    setattr(self.bkr_xml, key, value)

        # generate beaker job xml (workflow-simple command)
        self.bkr_xml.generate_beaker_xml(
            bkr_xml_file, kickstart_path=self.workspace, savefile=True
        )

        if 'force' in self.bkr_xml.hrname:
            self.logger.warning('Force was specified as a host_require_option. '
                                'Any other host_require_options will be ignored since '
                                'force is a mutually exclusive option in beaker.')
        # format beaker client command to run
        # Latest version of beaker client fails to generate xml with this
        # replacement
        # _cmd = self.bkr_xml.cmd.replace('=', "\=")

        self.logger.info('Generating beaker job XML..')
        self.logger.debug('Command to be run: %s' % self.bkr_xml.cmd)

        # generate beaker job XML
        results = exec_local_cmd(self.bkr_xml.cmd)
        if results[0] != 0:
            self.logger.error(results[2])
            raise BeakerProvisionerError('Failed to generate beaker job XML!')
        output = results[1]

        # generate complete beaker job XML
        self.bkr_xml.generate_xml_dom(bkr_xml_file, output, savefile=True)
        self.logger.info('Successfully generated beaker job XML!')

    def submit_bkr_xml(self):
        """Submit a beaker job XML to Beaker.

        This method will upload (submit) a beaker job XML to Beaker. If the
        job was successfully uploaded, the beaker job id will be returned.
        """
        # setup beaker client job submit commnand
        _cmd = "bkr job-submit --xml %s" % os.path.join(
            self.data_folder, self.job_xml)

        self.logger.info('Submitting beaker job XML..')
        self.logger.debug('Command to be run: %s' % _cmd)

        # submit beaker XML
        results = exec_local_cmd(_cmd)
        if results[0] != 0:
            self.logger.error(results[2])
            raise BeakerProvisionerError('Failed to submit beaker job XML!')
        output = results[1]

        # post results tasks
        if output.find("Submitted:") != "-1":
            mod_output = output[output.find("Submitted:"):]

            # set the result as ascii instead of unicode
            job_id = mod_output[mod_output.find(
                "[") + 2:mod_output.find("]") - 1]
            job_url = os.path.join(self.url, 'jobs', job_id[2:])

            self.logger.info('Beaker job ID: %s.' % job_id)
            self.logger.info('Beaker job URL: %s.' % job_url)

            self.logger.info('Successfully submitted beaker XML!')

            return job_id, job_url

    def wait_for_bkr_job(self, job_id):
        """Wait for submitted beaker job to have complete status.

        This method will wait for the beaker job to be complete depending on
        the timeout set. Users can define their own custom timeout or it will
        wait indefinitely for the machine to be provisioned.
        """
        # set max wait time (default is 8 hours)
        wait = self.provider_params.get('bkr_timeout', None)
        if wait is None:
            wait = 28800

        self.logger.debug('Beaker timeout limit: %s.' % wait)

        # check Beaker status every 60 seconds
        total_attempts = int(wait / 60)

        attempt = 0
        while wait > 0:
            attempt += 1
            self.logger.info('Waiting for machine to be ready, attempt %s of '
                             '%s.' % (attempt, total_attempts))

            # setup beaker job results command
            _cmd = "bkr job-results %s" % job_id

            self.logger.debug('Fetching beaker job status..')

            # fetch beaker job status
            results = exec_local_cmd(_cmd)
            if results[0] != 0:
                self.logger.error(results[2])
                raise BeakerProvisionerError('Failed to fetch job status!')
            xml_output = results[1]

            self.logger.debug('Successfully fetched beaker job status!')

            bkr_job_status_dict = self.get_job_status(xml_output)
            self.logger.debug("Beaker job status: %s" % bkr_job_status_dict)
            status = self.analyze_results(bkr_job_status_dict)

            self.logger.info('Beaker Job: id: %s status: %s.' %
                             (job_id, status))

            if status == "wait":
                wait -= 60
                time.sleep(60)
                continue
            elif status == "success":
                self.logger.info("Machine is successfully provisioned from "
                                 "Beaker!")
                # get machine info
                return self.get_machine_info(xml_output)
            elif status == "fail":
                raise BeakerProvisionerError(
                    'Beaker job %s provision failed!' % job_id
                )
            else:
                raise BeakerProvisionerError(
                    'Beaker job %s has unknown status!' % job_id
                )

        # timeout reached for Beaker job
        self.logger.error('Maximum number of attempts reached!')

        # cancel job
        self.cancel_job(job_id)

        raise BeakerProvisionerError(
            'Timeout reached waiting for beaker job to finish!'
        )

    def create(self):
        """Create a new job in Beaker.

        This method will create a Beaker job xml based on host information,
        submit the job to Beaker and wait for the job to be complete.
        """
        self.logger.debug('Provisioning machines from %s', self.__class__)

        # authenticate with beaker
        self.authenticate()

        # generate beaker job xml
        self.gen_bkr_xml()

        # submit beaker job xml and get beaker job id
        job_id, job_url = self.submit_bkr_xml()

        # wait for the bkr job to be complete and return pass or failed
        hostname, ip = self.wait_for_bkr_job(job_id)

        # copy ssh key to remote system
        if 'ssh_key' in self.provider_params and self.provider_params.get('ssh_key', None):
            self.logger.info('Inject SSH key into remote machine.')
            self.copy_ssh_key(hostname, ip)
        else:
            self.logger.warning('No SSH key defined, skip injecting key.')

        return [dict(asset_id=job_id, job_url=job_url, hostname=hostname, ip=ip)]

    def cancel_job(self, job_id):
        """Cancel a existing beaker job.

        This method will cancel a existing beaker job using the job id.
        """

        # setup beaker job cancel command
        _cmd = "bkr job-cancel {0}".format(job_id)

        self.logger.info('Canceling beaker job..')

        # cancel beaker job
        results = exec_local_cmd(_cmd)
        if results[0] != 0:
            self.logger.error(results[2])
            raise BeakerProvisionerError('Failed to cancel job.')
        output = results[1]

        if "Cancelled" in output:
            self.logger.info("Job %s cancelled." % job_id)
        else:
            raise BeakerProvisionerError('Failed to cancel beaker job!')

        self.logger.info('Successfully cancelled beaker job!')

    def delete(self):
        """Delete a beaker job to release system back to the pool.

        This method will cancel a existing beaker job based on beaker job id.
        """
        self.logger.info('Tearing down machines from %s', self.__class__)

        # authenticate with beaker
        self.authenticate()

        # cancel beaker job
        self.cancel_job(getattr(self.asset, 'asset_id'))

    def validate(self):
        schema_validator(schema_data=self.build_profile(self.asset), schema_files=[self.__schema_file_path__])

    def get_job_status(self, xmldata):
        """Parse the beaker results.

        :param xmldata: XML data from beaker job status fetched.
        :type xmldata: str
        :return: Install (task) results
        :rtype: dict
        """
        mydict = {}
        # parse xml data string
        try:
            dom = parseString(xmldata)
        except Exception as ex:
            raise BeakerProvisionerError(
                'Failed reading XML data: %s.' % ex
            )

        # check job status
        joblist = dom.getElementsByTagName('job')

        # verify it is a length of 1 else exception
        if len(joblist) != 1:
            raise BeakerProvisionerError(
                'Unable to parse job results from %s.' % self.provider_params.get('job_id')
            )

        mydict["job_result"] = joblist[0].getAttribute("result")
        mydict["job_status"] = joblist[0].getAttribute("status")

        tasklist = dom.getElementsByTagName('task')

        for task in tasklist:
            cname = task.getAttribute('name')
            if cname == '/distribution/install' or cname == '/distribution/check-install':
                mydict["install_result"] = task.getAttribute('result')
                mydict["install_status"] = task.getAttribute('status')

        if "install_status" in mydict and mydict["install_status"]:
            return mydict
        else:
            raise BeakerProvisionerError('Could not find install task status!')

    def get_machine_info(self, xmldata):
        """Get the remote system information from the beaker results XML.

        This method will parse the beaker results XML to get the hostname and
        IP address.

        :param xmldata: XML data of a beaker job status.
        :type xmldata: dict
        """
        try:
            dom = parseString(xmldata)
        except Exception as ex:
            raise BeakerProvisionerError(
                'Failed reading XML data: %s.' % ex
            )

        tasklist = dom.getElementsByTagName('task')
        for task in tasklist:
            cname = task.getAttribute('name')

            if cname == '/distribution/install' or cname == '/distribution/check-install':
                hostname = task.getElementsByTagName('system')[0]. \
                    getAttribute("value")
                addr = socket.gethostbyname(hostname)
                try:
                    hostname = hostname.split('.')[0]
                except Exception:
                    pass

                return hostname, addr

    def copy_ssh_key(self, hostname, ip):
        """Copy SSH public key to remote system.

        This method will inject the public SSH key into remote system. It
        will create the public key content from the private key given.
        """

        ssh_key = self.provider_params.get('ssh_key')
        username = self.provider_params.get('username')
        password = self.provider_params.get('password')

        # setup absolute path for private key
        private_key = os.path.join(self.workspace, ssh_key)

        # set permission of the private key
        try:
            os.chmod(private_key, stat.S_IRUSR | stat.S_IWUSR)
        except OSError as ex:
            raise BeakerProvisionerError(
                'Error setting private key file permissions: %s' % ex
            )

        self.logger.info('Generating SSH public key from private..')

        # generate public key from private
        public_key = os.path.join(
            self.workspace, ssh_key + ".pub"
        )
        rsa_key = paramiko.RSAKey(filename=private_key)
        with open(public_key, 'w') as f:
            f.write('%s %s\n' % (rsa_key.get_name(), rsa_key.get_base64()))

        self.logger.info('Successfully generated SSH public key from private!')

        self.logger.info('Send SSH key to remote system %s:%s' %
                         (hostname, ip))

        # send the key to the beaker machine
        ssh_con = paramiko.SSHClient()
        ssh_con.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        ssh_dir = "/root/.ssh"

        try:
            ssh_con.connect(hostname=ip,
                            username=username,
                            password=password)
            sftp = ssh_con.open_sftp()

            try:
                sftp.stat(ssh_dir)
            except FileNotFoundError:
                self.logger.warning(f"Directory {ssh_dir} does not exist on {ip}. Creating directory "
                                    f"before sending key.")
                sftp.mkdir(ssh_dir, mode=0o755)

            sftp.put(public_key, f"{ssh_dir}/authorized_keys")
        except paramiko.SSHException as ex:
            raise BeakerProvisionerError(
                'Failed to connect to remote system: %s' % ex
            )
        except IOError as ex:
            raise BeakerProvisionerError(
                'Failed sending public key: %s' % ex
            )
        finally:
            ssh_con.close()

        self.logger.debug("Successfully sent key: {0}, "
                          "{1}".format(ip,
                                       hostname))

    def analyze_results(self, resultsdict):
        """Analyze the beaker job install task status.
        return success, fail, or warn based on the job and install task statuses

        :param resultsdict: Beaker job of install task status.
        :rtype: dict
        :return: Action such as [wait, success or fail]
        :rtype: str
        """
        # when is the job complete
        # TODO: explain what each beaker results analysis means
        if resultsdict["job_result"].strip().lower() == "new" and \
                resultsdict["job_status"].strip().lower() in \
                ["new", "waiting", "queued", "scheduled", "processed",
                 "installing"]:
            return "wait"
        elif resultsdict["install_result"].strip().lower() == "new" and \
                resultsdict["install_status"].strip().lower() in \
                ["new", "waiting", "queued", "scheduled", "running",
                 "processed"]:
            return "wait"
        elif resultsdict["job_status"].strip().lower() == "waiting" or \
                resultsdict["install_status"].strip().lower() == "waiting":
            return "wait"
        elif resultsdict["job_result"].strip().lower() == "pass" and \
                resultsdict["job_status"].strip().lower() == "running" and \
                resultsdict["install_result"].strip().lower() == "pass" and \
                resultsdict["install_status"].strip().lower() == "completed":
            return "success"
        elif resultsdict["job_result"].strip().lower() == "new" and \
                resultsdict["job_status"].strip().lower() == "running" and \
                resultsdict["install_result"].strip().lower() == "new" and \
                resultsdict["install_status"].strip().lower() == "completed":
            return "success"
        elif resultsdict["job_result"].strip().lower() == "warn":
            return "fail"
        elif resultsdict["job_result"].strip().lower() == "fail":
            return "fail"
        else:
            raise BeakerProvisionerError(
                'Unexpected job status: %s!' % resultsdict
            )


class BeakerXML(object):
    """ Class to generate Beaker XML file from input host yaml"""
    _op_list = ['like', '==', '!=', '<=', '>=', '=', '<', '>']

    def __init__(self):
        """Intialization of BeakerXML"""
        self._jobgroup = ""
        self._key_values = ""
        self._xmldom = ""
        self._arch = ""
        self._family = ""
        self._component = ""
        self._cmd = ""
        self._runid = ""
        self._osvariant = ""
        self._retention_tag = ""
        self._whiteboard = ""
        self._method = "nfs"
        self._reservetime = "86400"
        self._host_requires_options = []
        self._distro_requires_options = []
        self._tasklist = []
        self._paramlist = []
        self._hrname = []
        self._hrvalue = []
        self._taskparam = []
        self._hrop = []
        self._drname = []
        self._drvalue = []
        self._drop = []
        self._tag = ""
        self._priority = "Normal"  # Low, Medium, Normal, High, or Urgent
        self._distro = ""
        self._kernel_options = ""
        self._kernel_options_post = ""
        self._kickstart = ""
        self._ksmeta = ""
        self._ksappends = []
        self._remove_task = False
        self._virtmachine = False
        self._virtcapable = False
        self._ignore_panic = False

    def generate_beaker_xml(self, x, kickstart_path='/tmp', savefile=False):

        xmlfile = x

        # How will we generate the XML dom
        # Step 1: take all the values and pass it to bkr workflow simple to create a xml for us.
        with open(xmlfile, 'w+') as fp:
            fp.write("<?xml version='1.0' ?>\n")

        # Set virtual machine if configured
        if self.virtual_machine:
            self.sethostrequires('hypervisor', '!=', "")

        # Set virtual capable if configured
        if self.virt_capable:
            self.sethostrequires('system_type', '=', "Machine")
            self.setdistrorequires('distro_virt', '=', "")

        # Set User supplied host requires
        if self.host_requires_options:
            for hro in self.host_requires_options:
                for hro_op in self._op_list:
                    if hro_op in hro:
                        hr_values = hro.split(hro_op)
                        self.sethostrequires(hr_values[0].strip(),
                                             hro_op, hr_values[1].strip())
                        break

        # Set User supplied host requires
        if self.distro_requires_options:
            for dro in self.distro_requires_options:
                for dro_op in self._op_list:
                    if dro_op in dro:
                        dr_values = dro.split(dro_op)
                        self.setdistrorequires(dr_values[0].strip(),
                                               dro_op, dr_values[1].strip())
                        break

        # Set User supplied taskparam Only valid option currently is reservetime
        if self.taskparam:
            for taskparam in self.taskparam:
                for tp_op in self._op_list:
                    if tp_op in taskparam:
                        tp_values = taskparam.split(tp_op)
                        tp_key = str(tp_values[0]).lower()
                        if tp_key == 'reservetime':
                            self.reservetime = tp_values[1]
                            break
                        else:
                            raise AttributeError(
                                "taskparam setting of %s not currently supported." %
                                tp_key)

        # Set arch
        self.cmd += "bkr workflow-simple --arch " + self.arch

        # Generate Whiteboard Value if not specified
        if self.whiteboard == "":
            self.whiteboard = "Teflo:"
            if self.runid != "":
                self.whiteboard += " RunID:" + self.runid
            if self.component != "":
                self.whiteboard += " Component:" + self.component
            if self.distro != "":
                self.whiteboard += " " + self.distro
            else:
                self.whiteboard += " " + self.family + "," + self.tag
            self.whiteboard += " " + self.arch

        # Set family if configured and no distro specified
        if self.family != "" and self.distro == "":
            self.cmd += " --family " + self.family

        # Set variant if configured
        if self.variant != "":
            self.cmd += " --variant " + self.variant

        # Set retention tag
        if self.retention_tag != "":
            self.cmd += " --retention_tag " + self.retention_tag

        # Set whiteboard and method
        self.cmd += " --whiteboard '" + self.whiteboard + "'"
        self.cmd += " --method " + self.method

        # Set kernel options
        if self.kernel_options != "":
            self.cmd += " --kernel_options '" + " ".join(
                self.kernel_options) + "'"

        # Set post kernel options
        if self.kernel_post_options != "":
            self.cmd += " --kernel_options_post '" + " ".join(
                self.kernel_post_options) + "'"

        # Set kickstart file
        if self.kickstart != "":
            self.cmd += " --kickstart '" + kickstart_path + "/" + self.kickstart + "'"

        # Set kick start meta options
        if self.ksmeta != "":
            self.cmd += " --ks-meta '" + " ".join(self.ksmeta) + "'"

        # Set kickstart append script
        if self.ksappends != []:
            for ksappend in self.ksappends:
                self.cmd += " --ks-append '" + ksappend + "'"

        # Set debug and dryrun
        self.cmd += " --debug --dryrun"

        # Removal of --prettyxml option because it creates too many line breaks.
        # self.cmd += " --prettyxml"

        # workaround for no tasks, add one task and delete it later
        self.cmd += " --task " + "/distribution/reservesys"
        self._remove_task = True

        # Set tag if distro empty else distro
        if self.tag:
            self.cmd += " --tag " + self.tag

        if self.distro:
            self.cmd += " --distro " + self.distro

        # Set ignore panic
        if self.ignore_panic:
            self.cmd += " --ignore-panic"

        # Set job group
        if self.jobgroup != "":
            self.cmd += " --job-group " + self.jobgroup

        # Set priority
        self.cmd += " --priority " + self.priority

        # Set a key value hostrequires field
        for kv in self.key_values:
            self.cmd += " --keyvalue '" + kv + "'"

    def generate_xml_dom(self, x, xmldata, savefile=False):

        xmlfile = x

        with open(xmlfile, 'w+') as fp:
            for xmlline in xmldata:
                fp.write(xmlline)

        # parse the xml that was create and put it into a dom, so it can be modified
        dom1 = parse(xmlfile)
        # print dom1.toprettyxml()

        # Done with the xmlfile so it can be deleted
        if not savefile:
            os.remove(xmlfile)

        # If there were no tasks added delete the one placeholder task, which
        # was added because one task must be passed to simple workflow
        if self._remove_task:
            recipe_parent = dom1.getElementsByTagName('recipe')[0]
            tasklength = dom1.getElementsByTagName('task').length
            delete_index = tasklength - 1
            delete_element = dom1.getElementsByTagName('task')[delete_index]
            # print tasklength
            # print delete_index
            # print delete_element
            recipe_parent.removeChild(delete_element)

        # Step 2: Take the xml generated by beaker-workflow and put it into a DOM
        # Create host requires  elementi
        if len(dom1.getElementsByTagName('and')) > 1:
            hre_parent = dom1.getElementsByTagName('and')[1]
        elif 'force' not in self.hrname:
            temp_parent = dom1.getElementsByTagName('hostRequires')[0]
            # print temp_parent
            temp_parent.appendChild(dom1.createElement('and'))
            # print dom1.toprettyxml()
            hre_parent = dom1.getElementsByTagName('and')[1]

        dre_parent = dom1.getElementsByTagName('and')[0]

        # should check for an empty host requires first
        if self.hrname:
            if 'force' in self.hrname:
                index = self.hrname.index('force')
                hre = dom1.getElementsByTagName('hostRequires')[0]
                hre.attributes[str(self.hrname[index])] = str(self.hrvalue[index])
            else:
                for index, value in enumerate(self.hrname):
                    # parse the value hostrequires key, first is op the rest is the value
                    # print str(self.hrname[index])
                    # print str(self.hrop[index])
                    # print str(self.hrvalue[index])
                    # Add all host requires here
                    hre = dom1.createElement(str(self.hrname[index]))
                    hre.attributes['op'] = str(self.hrop[index])
                    hre.attributes['value'] = str(self.hrvalue[index])

                    hre_parent.appendChild(hre)

        # should check for an empty distro requires first
        if self.drname:
            for index, value in enumerate(self.drname):
                # parse the value hostrequires key, first is op the rest is the value
                # Add all distro requires here
                dre = dom1.createElement(str(self.drname[index]))
                dre.attributes['op'] = str(self.drop[index])
                dre.attributes['value'] = str(self.drvalue[index])

                dre_parent.appendChild(dre)

        # Reserve if it fails
        te = dom1.createElement('task')
        te.attributes['name'] = "/distribution/reservesys"
        te.attributes['role'] = "STANDALONE"

        tpe = dom1.createElement('params')

        tpce = dom1.createElement('param')
        # tpce.attributes['name'] = "RESERVE_IF_FAIL"
        # tpce.attributes['value'] = "true"

        tpce2 = dom1.createElement('param')
        tpce2.attributes['name'] = "RESERVETIME"
        tpce2.attributes['value'] = str(self.reservetime)

        te_parent = dom1.getElementsByTagName("recipe")[0]

        # Add reservetime to the xml
        te_parent.appendChild(te)
        te.appendChild(tpe)
        tpe.appendChild(tpce)
        tpe.appendChild(tpce2)

        # set the completed DOM and return 0 for a successfull creation of the Beaker XML
        self.xmldom = dom1

        # Output updated file
        with open(xmlfile, "w+") as fp:
            self.xmldom.writexml(fp)

    @property
    def kernel_post_options(self):
        """Return the kernel post options."""
        return self._kernel_options_post

    @kernel_post_options.setter
    def kernel_post_options(self, options):
        """Set the the kernel post options.
        :param options: post kernel options"""
        self._kernel_options_post = options

    @property
    def kernel_options(self):
        """Return the beaker options."""
        return self._kernel_options

    @kernel_options.setter
    def kernel_options(self, options):
        """Set the beaker options.
        :param options: beakeroptions"""
        self._kernel_options = options

    @property
    def kickstart(self):
        """Return the kickstart file."""
        return self._kickstart

    @kickstart.setter
    def kickstart(self, ksfile):
        """Set kick start file.
        :param ksfile: kickstart file"""
        self._kickstart = ksfile

    @property
    def ksmeta(self):
        """Return the kick start meta data."""
        return self._ksmeta

    @ksmeta.setter
    def ksmeta(self, meta):
        """Set kick start meta data.
        :param meta: meta data"""
        self._ksmeta = meta

    @property
    def ksappends(self):
        """Return the kick start append scripts."""
        return self._ksappends

    @ksappends.setter
    def ksappends(self, scripts):
        """Set kick start append scripts.
        :param scripts: ksappend scripts"""
        self._ksappends = scripts

    @property
    def arch(self):
        """Return the arch."""
        return self._arch

    @arch.setter
    def arch(self, arch):
        """Set arch for resource.
        :param arch: Arch of resource"""
        self._arch = arch

    @property
    def family(self):
        """Return the family of resource."""
        return self._family

    @family.setter
    def family(self, family):
        """Set family of resource.
        :param family: Family of resource"""
        self._family = family

    @property
    def ignore_panic(self):
        """Return the ignore_panic setting."""
        return self._ignore_panic

    @ignore_panic.setter
    def ignore_panic(self, ipbool):
        """Set ignore panic.
        :param ipbool: ignore panic setting (bool)"""
        self._ignore_panic = ipbool

    @property
    def retention_tag(self):
        """Return the retention tag."""
        return self._retention_tag

    @retention_tag.setter
    def retention_tag(self, rtag):
        """Set retention tag.
        :param rtag: Retention tag"""
        self._retention_tag = rtag

    @property
    def tag(self):
        """Return the tag."""
        return self._tag

    @tag.setter
    def tag(self, tag):
        """Set tag.
        :param tag: Tag to set"""
        self._tag = tag

    @property
    def jobgroup(self):
        """Return the jobs group."""
        return self._jobgroup

    @jobgroup.setter
    def jobgroup(self, group):
        """Set the jobs group.
        :param group: Group to use for job"""
        self._jobgroup = group

    @property
    def component(self):
        """Return the component."""
        return self._component

    @component.setter
    def component(self, component):
        """Set component.
        :param component: Component"""
        self._component = component

    @property
    def distro(self):
        """Return the distro."""
        return self._distro

    @distro.setter
    def distro(self, distro):
        """Set the distro for resource.
        :param distro: Distro to set"""
        self._distro = distro

    @property
    def method(self):
        """Return the method."""
        return self._method

    @method.setter
    def method(self, method):
        """ Set the method.
        :param method: Method to set"""
        self._method = method

    @property
    def priority(self):
        """Return the priority."""
        return self._priority

    @priority.setter
    def priority(self, priority):
        """Set priority.
        :param priority: Priority to set."""
        self._priority = priority

    @property
    def xmldom(self):
        """Return the xmldom."""
        return self._xmldom

    @xmldom.setter
    def xmldom(self, xmldom):
        """Set xmldom for class.
        :param xmldom"""
        self._xmldom = xmldom

    def get_xmldom_pretty(self):
        """Return the xmldom in pretty print format."""
        return self._xmldom.toprettyxml()

    @property
    def whiteboard(self):
        """Return the white board."""
        return self._whiteboard

    @whiteboard.setter
    def whiteboard(self, whiteboard):
        """Set whiteboard value.
        :param whiteboard: Value to set"""
        self._whiteboard = whiteboard

    @property
    def runid(self):
        """Return the runid of job ."""
        return self._runid

    @runid.setter
    def runid(self, runid):
        """Set runid.
        :param runid: runid of job"""
        self._runid = runid

    @property
    def paramlist(self):
        """Return the parameter list to be used by tasks."""
        return self._paramlist

    @paramlist.setter
    def paramlist(self, paramdict):
        """Set parameter list.
        :param paramdict: Paramerters to be used by tasklist (dict)."""
        raise AttributeError('You cannot set paramlist directly. '
                             'Use settaskparam().')

    @property
    def key_values(self):
        """Return the key values."""
        return self._key_values

    @key_values.setter
    def key_values(self, key_values):
        """Set key values for job.
        :param key_values: Key values to set for job"""
        self._key_values = key_values

    @property
    def taskparam(self):
        """Return the taskparam list. Its a list of task parameters
           that will be applied to all tasks"""
        return self._taskparam

    @taskparam.setter
    def taskparam(self, taskparam):
        """Set List of taskparam.
        :param taskparam: List of task parameter that will be applied to all tasks"""
        self._taskparam = taskparam

    @property
    def tasklist(self):
        """Return the task list."""
        return self._tasklist

    @tasklist.setter
    def tasklist(self, task):
        """Set List of tasks for job.
        :param task: List of tasks"""
        raise AttributeError('You cannot set tasklist directly. '
                             'Use settaskparam().')

    @property
    def host_requires_options(self):
        """Return the host requires options."""
        return self._host_requires_options

    @host_requires_options.setter
    def host_requires_options(self, hr_values):
        """Set host requires opttions.
        :param hr_values: List of host requires options"""
        self._host_requires_options = hr_values

    @property
    def distro_requires_options(self):
        """Return the distro requires options."""
        return self._distro_requires_options

    @distro_requires_options.setter
    def distro_requires_options(self, dr_values):
        """Set distro requires options.
        :param dr_values: List of distro requires options"""
        self._distro_requires_options = dr_values

    @property
    def hrname(self):
        """Return the host requires names."""
        return self._hrname

    @hrname.setter
    def hrname(self, hr_name):
        """Raises an exception when trying to set the host requires name
        directly. Must use sethostrequires.
        :param hr_name: The host requires name.
        """
        raise AttributeError('You cannot set Hostrequires name directly. '
                             'Use sethostrequires().')

    @property
    def hrop(self):
        """Return the host requires operations"""
        return self._hrop

    @hrop.setter
    def hrop(self, hr_op):
        """Raises an exception when trying to set the host requires op
        directly. Must use sethostrequires.
        :param hr_op: The host requires operation.
        """
        raise AttributeError('You cannot set Hostrequires operation directly. '
                             'Use sethostrequires().')

    @property
    def hrvalue(self):
        """Return the host requires values"""
        return self._hrvalue

    @hrvalue.setter
    def hrvalue(self, hr_value):
        """Raises an exception when trying to set the host requires value
        directly. Must use sethostrequires.
        :param hr_value: The host requires value.
        """
        raise AttributeError('You cannot set Hostrequires value directly. '
                             'Use sethostrequires().')

    @property
    def drname(self):
        """Return distro requires names"""
        return self._drname

    @drname.setter
    def drname(self, dr_name):
        """Raises an exception when trying to set the Distro requires name
        directly. Must use setdistrorequires.
        :param dr_name: The disto requires name.
        """
        raise AttributeError('You cannot set Distrorequires name directly. '
                             'Use setdistrorequires().')

    @property
    def drop(self):
        """Return distro requires operations"""
        return self._drop

    @drop.setter
    def drop(self, dr_op):
        """Raises an exception when trying to set the distro requires op
        directly. Must use setdistrorequires.
        :param dr_op: The distro requires operation.
        """
        raise AttributeError(
            'You cannot set Distrorequires operation directly. '
            'Use setdistrorequires().')

    @property
    def drvalue(self):
        """Return distro requires values"""
        return self._drvalue

    @drvalue.setter
    def drvalue(self, dr_value):
        """Raises an exception when trying to set the distro requires value
        directly. Must use setdistrorequires.
        :param dr_value: The distro requires value.
        """
        raise AttributeError('You cannot set Distroequires value directly. '
                             'Use setdistrorequires().')

    @property
    def cmd(self):
        """Return the bkr cmd to create xml."""
        return self._cmd

    @cmd.setter
    def cmd(self, cmd):
        """Set bkr cmd to run to create xml.
        :param cmd: bkr xml creation cmd"""
        self._cmd = cmd

    @property
    def virtual_machine(self):
        """Return the virtual machine setting."""
        return self._virtmachine

    @virtual_machine.setter
    def virtual_machine(self, vbool):
        """Set virtual machine setting.
        :param vbool: virtual machine setting (bool)"""
        self._virtmachine = vbool

    @property
    def virt_capable(self):
        """Return the virt capable setting."""
        return self._virtcapable

    @virt_capable.setter
    def virt_capable(self, vbool):
        """Set virt capable.
        :param vbool: virtual capable setting (bool)"""
        self._virtcapable = vbool

    @property
    def variant(self):
        """Return the variant."""
        return self._osvariant

    @variant.setter
    def variant(self, osvariant):
        """Set variant of resource.
        :param osvariant: variant of resource"""
        self._osvariant = osvariant

    @property
    def reservetime(self):
        """Return the reserve time."""
        return self._reservetime

    @reservetime.setter
    def reservetime(self, reservetime):
        """Set reserve time.
        :param reservetime: time to reserve resource for (seconds)"""
        self._reservetime = reservetime

    def get_xml_text(self):
        """Returns pretty print format of xml"""
        return self.xmldom.toprettyxml()

    def sethostrequires(self, hr_name, hr_op, hr_value):
        """Set host requires parameters.
        :param hr_name: Host requires name
        :param hr_op: Host requires operation
        :param hr_value: Host requires value"""
        self._hrname.append(hr_name)
        self._hrop.append(hr_op)
        self._hrvalue.append(hr_value)

    def setdistrorequires(self, dr_name, dr_op, dr_value):
        """Set the distro requires parameters.
        :param dr_name: Distro requires name
        :param dr_op: Distro requires operation
        :param dr_value: Distro requires value"""
        if dr_name not in self._drname:
            self._drname.append(dr_name)
            self._drop.append(dr_op)
            self._drvalue.append(dr_value)
        else:
            updateindex = self._drname.index(dr_name)
            self._drop[updateindex] = dr_op
            self._drvalue[updateindex] = dr_value

    def settaskparam(self, task, paramdict):
        self.tasklist.append(task)
        self.paramlist.append(paramdict)
