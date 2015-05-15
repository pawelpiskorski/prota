#!/c/Python27/python.exe
# -*- coding: utf-8 -*-

import pickle
import logging
import os.path
import argparse

logging.basicConfig(level=logging.DEBUG)

class Project:
    def __init__(self, fname="tasks.pickle"):

        if os.path.isfile(fname):
            logging.debug("loading " + fname)
            f = open(fname, 'r+')
            self.p = pickle.load(f)
            f.close()
        else:
            logging.error("no such file")
            self.start()

    def start(self):
        self.p = {
            'tid': 0,
            't': {
                0: {
                    'id': 0,
                    'm': 'the anonymous project',
                    's': 'running',
                    'ch': []
                    # no pid defined in root task
                }
            }
        }

    def tasks(self, idlist):
        for tid in idlist:
            yield self.p['t'][tid]

    def add_task(self, task={}, pid=0, peer_id=0):
        """
        inserts new task to list
        :param task: template dict of the task
        :param pid: parent id, root by default
        :param peer_id: preceding task id. zero appends at the end, nonzero overrides pid with parent of the peer.
        :return:
        """
        parent = self.p['t'][pid]
        peer = None
        if peer_id:
            peer = self.p['t'][peer_id]
            pid = peer['pid']
            parent = self.p['t'][pid]

        tid = self.p['tid'] + 1
        self.p['tid'] = tid
        task['id'] = tid
        task['pid'] = pid
        task['ch'] = []
        if 'm' not in task:
            task['m'] = 'task ' + str(tid)
        self.p['t'][tid] = task
        if peer:
            parent['ch'].insert(peer_id, tid)
        else:
            parent['ch'].append(tid)
        return task

    def rm_task(self, tid):
        """
        Removes task along with its subtasks.
        :param tid:
        :return:
        """
        if tid == 0:
            self.start()
            return

        task = self.p['t'][tid]
        for sub_id in task['ch']:
            self.rm_task(sub_id)

        self.p['t'].pop(tid)
        parent = self.p['t'][task['pid']]
        parent['ch'].remove(tid)

    def mv_task(self, tid, pid=0, peer_id=0):
        """
        moves a task
        :param tid: id of task to move
        :param pid: new parent id, root by default
        :param peer_id: new preceding task id. zero appends at the end, nonzero overrides pid with parent of the peer.
        :return:
        """
        task = self.p['t'][tid]
        old_parent = self.p['t'][task['pid']]
        # push under new parent
        if peer_id:
            pid = self.p['t'][peer_id]['pid']
            parent = self.p['t'][pid]
            parent['ch'].insert(peer_id, tid)
        else:
            parent = self.p['t'][pid]
            parent['ch'].append(tid)

        if pid == task['id']:
            raise Exception("task cannot be it's own parent")
        task['pid'] = pid
        # pop from old parent
        old_parent['ch'].remove(tid)

    def childrenids(self, tid):
        return self.p['t'][tid]['ch']

    def children(self, tid):
        return self.tasks(self.childrenids(tid))

    def save(self, fname="tasks.pickle"):
        logging.debug("saving file")
        f = open(fname, 'w')
        pickle.dump(self.p, f)
        f.close()

    def update(self, tid, task):
        if 'id' in task:
            del task['id']  # cannot change the task id
        self.p['t'][tid].update(task)

    def pprint(self, idlist, seek, indent=""):
        for t in self.tasks(idlist):
            if seek == 0 or seek == t['id']:
                print indent + '{0:04d}'.format(t['id']) + " " + t['m']
                self.pprint(t['ch'], 0, indent + " ")

    def list(self, seek):
        print self.p['t'][0]['m']
        self.pprint(self.childrenids(0), seek, ' ')


# commands

def start(params):
    logging.info("starting project: " + params.m)
    project = Project("")
    task = {
        'm': params.m
    }
    project.update(0, task)
    project.save()


def add(params):
    logging.info("adding task: " + params.m)
    task = {
        'm': params.m,
        'd': params.deadline,
        'o': params.owner,
        's': params.state
    }

    project = Project()

    project.add_task(dict((a, b) for (a, b) in task.iteritems() if b is not None),
                     pid=params.parent, peer_id=params.after)
    project.save()


def ls(params):
    logging.info("listing task: " + str(params.tid))
    project = Project()
    project.list(params.tid)


def edit(params):
    logging.info("editing task: " + str(params.tid))
    task = {
        'm': params.m,
        'd': params.deadline,
        'o': params.owner,
        's': params.state
    }

    project = Project()
    project.update(params.tid, dict((a, b) for (a, b) in task.iteritems() if b is not None))
    project.save()


def move(params):
    logging.info("moving task: " + str(params.tid))
    project = Project()
    project.mv_task(params.tid,  pid=params.parent, peer_id=params.after)
    project.save()


def remove(params):
    logging.info("deleting task: " + str(params.tid))
    project = Project()
    project.rm_task(params.tid)
    project.save()


parser = argparse.ArgumentParser(description='simple project TAsk management.')
subparsers = parser.add_subparsers()

subparser = subparsers.add_parser('start', help="start new project")
subparser.add_argument('m', type=unicode, help="project title")
subparser.set_defaults(func=start)

subparser = subparsers.add_parser('ls', help="list project file")
subparser.add_argument('tid', type=int, default=0, nargs='?', help="id of task to print, 0 (whole project) by default")
subparser.set_defaults(func=ls)

subparser = subparsers.add_parser('add', help="add new task")
subparser.add_argument('-p', '--parent', type=int, default=0, nargs='?', help="parent id for new task")
subparser.add_argument('-a', '--after', type=int, default=0, nargs='?', help="id of task that will precede new task")
subparser.add_argument('-d', '--deadline', type=unicode, nargs='?', default=None, help="deadline")
subparser.add_argument('-o', '--owner', type=unicode, nargs='?', default=None, help="owner")
subparser.add_argument('-s', '--state', choices=['pending', 'running', 'done'], nargs='?', default="pending", help="task state")
subparser.add_argument('m', type=unicode, help="task description")
subparser.set_defaults(func=add)

subparser = subparsers.add_parser('e', help="edit task")
subparser.add_argument('tid', type=int, default=0, help="task id")
subparser.add_argument('-d', '--deadline', type=unicode, nargs='?', default=None, help="deadline")
subparser.add_argument('-o', '--owner', type=unicode, nargs='?', default=None, help="owner")
subparser.add_argument('-s', '--state', choices=['pending', 'running', 'done'], nargs='?', default=None, help="task state")
subparser.add_argument('-m', type=unicode, default=None, help="task description")
subparser.set_defaults(func=edit)

subparser = subparsers.add_parser('rm', help="remove task")
subparser.add_argument('tid', type=int, default=0, help="id of parent task")
subparser.set_defaults(func=remove)

subparser = subparsers.add_parser('mv', help="move task(s)")
subparser.add_argument('tid', type=int, help="task to move")
subparser.add_argument('-p', '--parent', type=int, default=0, nargs='?', help="parent id for new task")
subparser.add_argument('-a', '--after', type=int, default=0, nargs='?', help="id of task that will precede new task")
subparser.set_defaults(func=move)


params = parser.parse_args()
logging.debug(str(params))
params.func(params)


