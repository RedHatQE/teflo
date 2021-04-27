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
    teflo.static.playbooks

    A module containing string representations of playbooks used by teflo.

    :copyright: (c) 2021 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""

SYNCHRONIZE_PLAYBOOK = '''
- name: fetch artifacts
  hosts: "{{ hosts }}"

  tasks:
    - name: find artifacts
      find:
        path: "{{ (item | regex_replace('/$', '')).split('/')[:-1] | join('/') }}"
        patterns: "{{ (item | regex_replace('/$', '')).split('/')[-1] }}"
        file_type: any
      with_items:
        - "{{ artifacts }}"
      register: found_artifacts
      {{ options }}

    - block:
        - name: setup artifacts_found list
          set_fact:
            artifacts_found: []

        - name: populate artifacts_found list
          set_fact:
            artifacts_found: "{{ artifacts_found + item.files }}"
          loop: "{{ found_artifacts.results }}"
          when: item.matched > 0

        - debug:
           msg: "{{ artifacts_found | length }}"

        - name: create localhost artifact directory
          file:
            path: "{{ dest }}/localhost/"
            state: directory
          delegate_to: localhost
          when: artifacts_found | length > 0

        - name: fetch local artifacts
          command:
            argv:
              - cp
              - -r
              - -v
              - "{{ item.path }}"
              - "{{ dest }}/localhost/"
          register: local_sync_output
          delegate_to: localhost
          loop: "{{ artifacts_found }}"
          {{ block_options }}
          when: artifacts_found | length > 0

        - name: copy skipped local artifacts results to file
          shell:
            echo -e "('{{ ansible_hostname }}', '{{ item.item }}', '', True, 0, )" \
            | sed -E ':a;N;$!ba;s/\\r{0,1}\\n/\\\\n/g' >> {{ 'sync-results-' + uuid }}.txt
          delegate_to: localhost
          loop: "{{ found_artifacts.results }}"
          when: artifacts_found | length == 0  or item.matched == 0

        - name: copy passed local artifacts results to file
          shell:
            echo -e "('{{ ansible_hostname }}', \'\'\'{{ item.stdout_lines | to_yaml \
            | regex_replace('[\\t|\\n|\\r|\\s]', '') | regex_replace("\\'", '') }}\'\'\', \
            '{{ item.cmd[-1] }}', False, 0, )" \
            | sed -E ':a;N;$!ba;s/\\r{0,1}\\n/\\\\n/g' | tr -d '\\r' >> {{ 'sync-results-' + uuid }}.txt
          delegate_to: localhost
          when: item is success and item is not skipped
          with_items:
            - "{{ local_sync_output.results }}"
      rescue:
        - name: copy failed local artifacts results to file
          shell:
            echo -e "('{{ ansible_hostname }}', '{{ item.item.path | to_yaml  \
            | regex_replace('[\\t|\\n|\\r|\\s]', '') }}', '', False, 1, )" \
            | sed -E ':a;N;$!ba;s/\\r{0,1}\\n/\\\\n/g' | tr -d '\\r' >> {{ 'sync-results-' + uuid }}.txt
          loop: "{{ local_sync_output.results }}"
          delegate_to: localhost
      when: localhost

    - block:
        - name: check if rsync package is installed
          command: 'rpm -q rsync'
          failed_when: false
          register: rsync_installed

        - name: install rsync
          package:
            name: rsync
            state: present
          become: true
          when: rsync_installed.rc != 0

        - name: fetch artifacts
          synchronize:
            src: "{{ item[1].item }}"
            dest: "{{ dest }}/{{ hostvars[item[0]]['ansible_hostname'] }}/"
            mode: pull
            recursive: yes
          with_nested:
            - "{{ inventory_hostname }}"
            - "{{ found_artifacts.results }}"
          register: sync_output
          {{ block_options }}
          when: item[1].matched > 0

        - name: copy skipped artifacts results to file
          shell:
            echo -e "('{{ ansible_hostname }}', '{{ item.item[1].item }}', '', True, 0, )" \
            | sed -E ':a;N;$!ba;s/\\r{0,1}\\n/\\\\n/g' >> {{ 'sync-results-' + uuid }}.txt
          delegate_to: localhost
          when: item is skipped
          with_items:
            - "{{ sync_output.results }}"

        - name: copy passed artifacts results to file
          shell:
            echo -e "('{{ ansible_hostname }}', \'\'\'{{ item.stdout_lines | to_yaml \
            | regex_replace('[\\t|\\n|\\r|\\s]', '') }}\'\'\', '{{ item.cmd.split(' ')[-1] }}', False, 0, )" \
            | sed -E ':a;N;$!ba;s/\\r{0,1}\\n/\\\\n/g' | tr -d '\\r' >> {{ 'sync-results-' + uuid }}.txt
          delegate_to: localhost
          when: item is success and item is not skipped
          with_items:
            - "{{ sync_output.results }}"

      rescue:
        - name: copy failed artifacts results to file
          shell:
            echo -e "('{{ ansible_hostname }}', '{{ item.item[1].item }}', '', False, 1, )" \
            | sed -E ':a;N;$!ba;s/\\r{0,1}\\n/\\\\n/g' | tr -d '\\r'>> {{ 'sync-results-' + uuid }}.txt
          delegate_to: localhost
          with_items:
            - "{{ sync_output.results }}"
      when: not localhost
'''

GIT_CLONE_PLAYBOOK = '''
- name: clone git repositories
  hosts: "{{ hosts }}"

  tasks:
    - name: check if git package is installed
      command: 'rpm -q git'
      failed_when: false
      register: git_installed

    - name: install git
      package:
        name: git
        state: present
      become: true
      when: git_installed.rc != 0

    - name: clone gits
      git:
        repo: "{{ item.repo }}"
        version: "{{ item.version }}"
        dest: "{{ item.dest }}"
      {{ options }}
      with_items:
        - "{{ gits }}"
'''

ADHOC_SHELL_PLAYBOOK = '''
- name: run shell and fetch results
  hosts: "{{ hosts }}"

  tasks:
    - name: shell command
      shell: "{{ xcmd }}"
      register: sh_results
      ignore_errors: true
      {{ args }}
      {{ options }}

    - name: to get correct (stderr/stdout/msg) output msg
      set_fact:
        sh_out: "{{  sh_results.stderr | default( sh_results.stdout )| default( sh_results.msg )|
                     default('stderr,stdout.msg NOT present in the output') }}"
    - name: setting json str
      set_fact:
        json_str: "{ 'host_name': '{{ ansible_facts.hostname}}', 'rc': '{{ sh_results.rc | default(1) }}',
                     'err': '{{ sh_out | regex_replace('\\\\s\\\\s+','')| regex_replace('\\n','')
                     | regex_replace(\\"'\\",'') }}' }"
    - name: copy to shell results to a json file
      copy:
        content: "{{ ansible_play_hosts | map('extract', hostvars, 'json_str') | list | to_nice_json }}"
        dest: ./{{ 'shell-results-' + uuid }}.json
      run_once: true
      delegate_to: localhost
'''

ADHOC_SCRIPT_PLAYBOOK = '''
- name: run script and fetch results
  hosts: "{{ hosts }}"

  tasks:
    - name: script command
      script: "{{ xscript }}"
      register: scrpt_results
      ignore_errors: true
      {{ args }}
      {{ options }}

    - name: to get correct (stderr/stdout/msg) output msg
      set_fact:
        scrpt_out: "{{  scrpt_results.stderr | default( scrpt_results.stdout )| default( scrpt_results.msg )|
                        default('stderr,stdout.msg NOT present in the output') }}"
    - name: setting json str
      set_fact:
        json_str: "{ 'host_name': '{{ ansible_facts.hostname}}', 'rc': '{{ scrpt_results.rc | default(1) }}',
                     'err': '{{ scrpt_out | regex_replace('\\\\s\\\\s+','')| regex_replace('\\n','')
                     | regex_replace(\\"'\\",'')}}' }"
    - name: copy to shell results to a json file
      copy:
        content: "{{ ansible_play_hosts | map('extract', hostvars, 'json_str') | list | to_nice_json }}"
        dest: ./{{ 'script-results-' + uuid }}.json
      run_once: true
      delegate_to: localhost
'''
