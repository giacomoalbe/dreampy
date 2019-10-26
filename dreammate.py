#!/usr/bin/env python3

import argparse
import sys
import os
import re
import subprocess
import fileinput
import yaml
import terminaltables

from todotxt import TodoFile, TodoEntry
from typing import List
from datetime import datetime, timedelta

usage_string = '''

dm <action> [<args>]

Available actions:
  start     Start tracking time for a given project
  pause     Pause current tracking by closing current time entry (with placeholder)
  commit    Ends currently open (last) time entry with the appropriate payload
  log       Get all time entries for a given project
  current   Get current active project
  restart   Restart a project after a pause. A custom datetime can be set
  tasks     Subcommand for handling everything related to tasks

'''

tasks_usage_string = '''

dm tasks <action> [<args>]

Available actions:
  add       Add a task to a project (default to active project)
  list      List all the tasks for a given project (default to active project)
  delete    Delete a task of a given project by providing its id

'''


def get_scm_commit_commands(scm, commit_message):
    if scm == 'git':
        return [
            ["git", "add", "."],
            ["git", "commit", "-m", commit_message]
        ]
    else:
        return []

class ActiveProject(object):
    def __init__(self, name, start_string = "", end_string=""):
        self.name = name
        self.start = self.parse_date_or_none(start_string)
        self.end = self.parse_date_or_none(end_string)
        self.isPaused = self.end != None

    def __str__(self):
        return "{}: [{}, {}] P: {}".format(
            self.name,
            self.start,
            self.end,
            self.isPaused
        )

    def parse_date_or_none(self, date_string):
        if date_string == "":
            return None

        date_string = date_string.split("###")[0].strip()

        date_format = "{} %Y/%m/%d %H:%M:%S".format(date_string[0])

        return datetime.strptime(date_string, date_format)

class TaskManager(object):
    def __init__(self, active_project: ActiveProject, cli_args: List[str]):
        parser = argparse.ArgumentParser(
            description="Manage task related activities",
            usage=tasks_usage_string
        )

        parser.add_argument(
            "action",
            help="Action to take"
        )

        args, _ = parser.parse_known_args(cli_args[0:1])

        # Action lookup inside class methods
        if not hasattr(self, args.action):
            print('ERROR: Action not recognized: {}'.format(args.action))
            print('')
            parser.print_help()
            exit(1)

        self.cli_args = cli_args[1:]
        self.active_project = active_project

        # Invoke action's relative function
        getattr(self, args.action)()

        pass

    def add(self):
        parser = argparse.ArgumentParser(
            description="Add different tasks to a project (default to active_project)",
            usage="dm tasks add [-h] [-p <project_name>] [-c <context>] [-r <priority>] [<task>]"
        )

        parser.add_argument(
            "-p",
            "--project",
            help="Project to add tasks to"
        )

        parser.add_argument(
            "-c",
            "--context",
            help="Context to add to the task (as defined in the project file configuration)"
        )

        parser.add_argument(
            "-r",
            "--priority",
            choices=["A", "B", "C", "D", "E", "F", "G"],
            help="Priority of the task to create"
        )

        parser.add_argument(
            'task',
            nargs='?',
            default=None
        )

        args = parser.parse_args(self.cli_args)

        self.cli_args = self.cli_args[1:]

        task_project = None
        task_context = None
        task_priority = None
        task_description = None

        if args.project:
            # TODO: check project exists
            task_project = ActiveProject(args.project)

        if args.context:
            # TODO: check context exists in project file
            task_context = args.context

        if args.priority:
            task_priority = args.priority

        if args.task and args.context and args.project:
            # Add task and exit
            task_entry = TodoEntry("")

            task_entry.add_tag("task", args.task)
            task_entry.add_project(task_project.name)
            task_entry.add_context(task_context)
            task_entry.created_date = datetime.now()
            task_entry.priority = task_priority

            self.save_tasks([task_entry], task_project)

            exit(0)

        save_tasks = False
        tasks: List[TodoEntry] = []

        while True:
            task_description: str = input("Insert task description (x to discard, s to save): ")

            if (task_description.strip().lower() == 'x'):
                break

            if (task_description.strip().lower() == 's'):
                save_tasks = True
                break

            if not task_project:
                project_name = input("Insert task project: ")
                task_project = ActiveProject(project_name)

            if not task_context:
                task_context = input("Insert task context: ")

            if not task_priority:
                task_priority: str = input("Insert task priority [A-G]: ")

            task_entry = TodoEntry("")

            task_entry.add_tag("task", task_description)
            task_entry.add_project(task_project.name)
            task_entry.add_context(task_context)
            task_entry.priority = task_priority
            task_entry.created_date = datetime.now()

            tasks.append(task_entry)

        if save_tasks:
            self.save_tasks(tasks, task_project)

        print("No tasks added")

    def list(self):
        parser = argparse.ArgumentParser(
            description="Get all task for a given project (defaults to active project)",
            usage="dm tasks list [-h] [-p <project_name>] [-n <number>]"
        )

        parser.add_argument(
            "-p",
            "--project",
            help="Project to show all tasks of"
        )

        parser.add_argument(
            "-n",
            "--number",
            type=int,
            help="Number of tasks to print to output"
        )

        args, _ = parser.parse_known_args(self.cli_args)

        limit = -1
        project: ActiveProject = self.active_project

        if args.number:
            limit = args.number

        if args.project:
            project = ActiveProject(args.project)

        todo_file = self.load_todo_file(project)

        if len(todo_file.todo_entries) == 0:
            print("No entries")
            exit(0)

        for index, entry in enumerate(todo_file.todo_entries):
            if limit > -1 and index == limit:
                break

            print(entry)

    def delete(self):
        pass

    def load_todo_file(self, project: ActiveProject):
        todo_file: TodoFile = TodoFile("{}_TODO.txt".format(project.name))

        try:
            todo_file.load()
        except:
            # Create file if it does not exists
            todo_file_name = "{}_TODO.txt".format(project.name)

            print("File: {} not found, creating it".format(todo_file_name))

            file_handle = open(todo_file_name, "w")
            file_handle.write("")

            todo_file.load()

        return todo_file

    def save_tasks(self, tasks: List[TodoEntry], project: ActiveProject):
        todo_file = self.load_todo_file(project)

        todo_file.add_entries(tasks, with_sort=True)

        todo_file.save()

        print("{} tasks saved in project {}".format(len(tasks), project.name))
        exit(0)

class DreamMate(object):
    """
    Lookup table with the value of dry_run
    (e.g active project not found triggers an exit)
    for each action
    """
    active_project = None
    actions_active_project_dry_run = {
        "start": True,
        "commit": False,
        "pause": False,
        "current": False,
        "restart": True,
        "tasks": True,
    }

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

        self.store_active_project_or_exit(args.action)

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

        if self.active_project.name == args.project:
            print("ERROR: Cannot start a project with the same name of the currently active project")
            print("Current project: {}\nProject to be started: {}".format(
                self.active_project.name,
                args.project
            ))
            exit(1)


        if self.active_project != None and not self.active_project.isPaused:
            self.pause()

        new_project = ActiveProject(
            args.project,
        )

        self.doStart(new_project, datetime.now())

        print("Started project: {}".format(self.active_project.name))

    def pause(self):
        if self.active_project.isPaused:
            print("ERROR: Cannot pause already paused project")
            exit(1)

        print("Pausing project: {}".format(self.active_project))
        self.doEnd(self.active_project, datetime.now())

    def commit(self):
        parser = argparse.ArgumentParser(
            description="Ends current activity on current project by setting a payload",
            usage="dm commit <message> [<args>]"
        )

        parser.add_argument('message', help="Message to use as payload")

        args = parser.parse_args(sys.argv[2:])

        if self.active_project.isPaused:
            print("ERROR: Cannot commit a paused active project, restart it beforehand")
            print("dm restart -d <restart_date>")
            exit(1)

        active_project_conf = self.load_project_configuration(self.active_project)

        if active_project_conf['isCode']:
            commit_commands = get_scm_commit_commands(
                active_project_conf['scm'],
                args.message
            )

            for command in commit_commands:
                try:
                    subprocess.check_output(
                        command,
                        stderr=subprocess.STDOUT,
                        cwd=os.path.expanduser(active_project_conf['root'])
                    )

                except subprocess.CalledProcessError as e:
                    print(e.output);
                    exit(1)

        end_time = datetime.now()

        self.doEnd(self.active_project, end_time)

        # Substitude each occurrence of ###<current_project>### with
        # <current_project>  <message>
        project_placeholder = "###{}###".format(self.active_project.name)
        project_account_payload = "{}  {}".format(self.active_project.name, args.message)

        with fileinput.FileInput("time.ledger", inplace=True, backup='.bak') as file:
            for line in file:
                print(line.replace(
                    project_placeholder,
                    project_account_payload
                ), end='')





        self.doStart(self.active_project, end_time + timedelta(seconds=10))

        print("Committing project: {} with message: {}".format(self.active_project, args.message))

    def current(self):
        print("Current project: {}".format(self.active_project))

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

    def restart(self):
        parser = argparse.ArgumentParser(
            description="Restart the current project so that changes can be committed. A custom datetime can be set as restart time",
            usage="dm restart -d <datetime> -p <project>"
        )

        parser.add_argument(
            '-d',
            '--datetime',
            help="Datetime in Y/m/d H:M to use as a restart date"
        )
        parser.add_argument(
            '-p',
            '--project',
            help="Project to restart if current project is not paused but already committed"
        )

        args = parser.parse_args(sys.argv[2:])

        restart_datetime = datetime.now()

        if (args.datetime != None):
            restart_datetime = datetime.strptime(args.datetime, "%Y/%m/%d %H:%M")

        if self.active_project == None or not self.active_project.isPaused:
            # Start a new task with current date set
            if not args.project:
                print("ERROR: Cannot restart active project: no active project!")
                print("Please provide one with -p <project_name>")
                exit(1)

            project_restarted = ActiveProject(args.project)
            self.doStart(project_restarted, restart_datetime)
        else:
            # Active project is paused, simply resart it with restart_datetime
            project_restarted = self.active_project

            if args.project != None:
                project_restarted = ActiveProject(
                    args.project
                )

            self.doStart(project_restarted, restart_datetime)

        print("Restarted project: {} on {}".format(project_restarted.name, restart_datetime))

    def tasks(self):
        taskManager = TaskManager(self.active_project, sys.argv[2:])


    # UTILS
    def store_active_project_or_exit(self, action):
        self.active_project = None

        if not action in self.actions_active_project_dry_run.keys():
            return

        self.active_project = self.find_last_active_project(
            action,
            dry_run=self.actions_active_project_dry_run[action]
        )

    def load_time_journal(self, mode = 'r'):
        return open("time.ledger", mode)

    def doStart(self, project, entry_time):
        start_time = self.get_time_string("start", entry_time, project)

        time_journal = self.load_time_journal('a')
        time_journal.write(start_time)
        time_journal.close()

    def doEnd(self, project, entry_time):
        end_time = self.get_time_string("end", entry_time, project)

        time_journal = self.load_time_journal('a')
        time_journal.write(end_time)
        time_journal.close()

    def get_time_string(self, side, entry_time: datetime, project: ActiveProject = None):
        if side == "start":
            return entry_time.strftime("i %Y/%m/%d %H:%M:%S ###{}###\n".format(project.name))
        elif side == "end":
            return entry_time.strftime("o %Y/%m/%d %H:%M:%S\n")
        else:
            print("ERROR: Unexpected side: {}".format(side))
            exit(1)

    def find_last_active_project(self, action = "", dry_run = False):
        active_project_re = re.compile('i.*###(.*)###')

        time_journal = self.load_time_journal('r')

        time_entries = time_journal.readlines()
        time_entries.reverse()

        active_project = None

        for index, line in enumerate(time_entries):
            project_found = active_project_re.findall(line)

            if (len(project_found)):
                active_project = ActiveProject(
                    project_found[0],
                    line,
                    # if line is the last line,
                    # it means that this project has not been
                    # paused
                    time_entries[index-1] if index > 0 else ""
                )
                break

        if active_project == None and not dry_run:
            print("ERROR: No current project found, nothing to {}!".format(action))
            exit(1)

        return active_project

    def load_project_configuration(self, project_name):
        try:
            file_content = open("{}.yaml".format(project_name.name), 'r')

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
