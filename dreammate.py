#!/usr/bin/env python3

import argparse
import sys
import os
import re
import subprocess
import fileinput
import yaml

from datetime import datetime

usage_string = '''

dm <action> [<args>]

Available actions:
  start     Start tracking time for a given project
  pause     Pause current tracking by closing current time entry (with placeholder)
  commit    Ends currently open (last) time entry with the appropriate payload
  log       Get all time entries for a given project
'''

def get_scm_commit_commands(scm, commit_message):
    if scm == 'git':
        return [
            ["git", "add", "."],
            ["git", "commit", "-m", commit_message]
        ]
    else:
        return []

class DreamMate(object):
    def __init__(self):
        parser = argparse.ArgumentParser(
            description="Your best Task Manager tool",
            usage=usage_string
        )

        parser.add_argument('action', help='Action to take')
        # Exclude args other than the first [1:2]
        args = parser.parse_args(sys.argv[1:2])

        # Action lookup inside class methods
        if not hasattr(self, args.action):
            print('ERROR: Action not recognized: {}'.format(args.action))
            print('')
            parser.print_help()
            exit(1)

        # Invoke action's relative function
        getattr(self, args.action)()

    # ACTIONS
    def start(self):
        parser = argparse.ArgumentParser(
            description="Start tracking time for a given project",
            usage="dm start <project> [<args>]"
        )

        parser.add_argument('project', help="Project to start tracking time for")

        args = parser.parse_args(sys.argv[2:])

        active_project = self.find_last_active_project("create", dry_run=True)

        if (active_project != ""):
            self.pause()

        start_time = self.get_time_string("start", args.project)

        time_journal = self.load_time_journal('a')
        time_journal.write(start_time)

    def pause(self):
        active_project = self.find_last_active_project("pause")

        print("Pausing project: {}".format(active_project))

        end_time = self.get_time_string("end")

        time_journal = self.load_time_journal('a')
        time_journal.write(end_time)

    def commit(self):
        parser = argparse.ArgumentParser(
            description="Ends current activity on current project by setting a payload",
            usage="dm commit <message> [<args>]"
        )

        parser.add_argument('message', help="Message to use as payload")

        args = parser.parse_args(sys.argv[2:])

        active_project = self.find_last_active_project("commit")
        active_project_conf = self.load_project_configuration(active_project)

        if active_project_conf['isCode']:
            commit_commands = get_scm_commit_commands(
                active_project_conf['scm'],
                args.message
            )

            for command in commit_commands:
                try:
                    command_output = subprocess.check_output(
                        command,
                        stderr=subprocess.STDOUT,
                        cwd=os.path.expanduser(active_project_conf['root'])
                    )

                except subprocess.CalledProcessError as e:
                    print(e.output);
                    exit(1)

        end_time = self.get_time_string("end")

        time_journal = self.load_time_journal('a')
        time_journal.write(end_time)
        time_journal.close()

        # Substitude each occurrence of ###<current_project>### with
        # <current_project>  <message>
        project_placeholder = "###{}###".format(active_project)
        project_account_payload = "{}  {}".format(active_project, args.message)

        with fileinput.FileInput("time.ledger", inplace=True, backup='.bak') as file:
            for line in file:
                print(line.replace(project_placeholder, project_account_payload), end='')
        print("Committing project: {} with message: {}".format(active_project, args.message))

    def log(self):
        parser = argparse.ArgumentParser(
            description="Get every time entry for a given project",
            usage="dm log <project> [<args>]"
        )

        parser.add_argument('project', help="Project to check time entries of")

        args = parser.parse_args(sys.argv[2:])

        p = subprocess.Popen([
            'ledger',
            'reg',
            '-f',
            'time.ledger',
            '--format',
            '%d|%15a|%-40P|%8t|\n',
            '--date-format',
            '%d/%m/%Y',
            args.project
        ], stdout=subprocess.PIPE)

        std_out, std_err = p.communicate()

        lines = std_out.decode('utf-8').split("\n")[:-1]

        for line in lines:
            print(line)

    # UTILS
    def load_time_journal(self, mode = 'r'):
        return open("time.ledger", mode)

    def get_time_string(self, side, project = ""):
        if side == "start":
            return datetime.now().strftime("i %Y/%m/%d %H:%M:%S ###{}###\n".format(project))
        elif side == "end":
            return datetime.now().strftime("o %Y/%m/%d %H:%M:%S\n")
        else:
            print("ERROR: Unexpected side: {}".format(side))
            exit(1)

    def find_last_active_project(self, action = "", dry_run = False):
        active_project_re = re.compile('i.*###(.*)###')

        time_journal = self.load_time_journal('r')

        time_entries = time_journal.readlines()
        time_entries.reverse()

        active_project = ""

        for line in time_entries:
            project_found = active_project_re.findall(line)

            if (len(project_found)):
                active_project = project_found[0]
                break

        if active_project == "" and not dry_run:
            print("ERROR: No current project found, nothing to {}!".format(action))
            exit(1)

        return active_project

    def load_project_configuration(self, project_name):
        try:
            file_content = open("{}.yaml".format(project_name), 'r')

            try:
                config = yaml.safe_load(file_content)
                return config

            except yaml.YAMLError as e:
                print("ERROR: Unable to load YAML configuration: {}".format(e))
                exit(1)

        except FileNotFoundError as e:
            print("ERROR: Project configuration not found! Not a known project")
            exit(1)

if __name__ == '__main__':
    DreamMate()
