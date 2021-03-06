#!/c/Python27/python.exe
# -*- coding: utf-8 -*-

import pickle
import logging
import os.path
import argparse
import difflib
import pprint
import sys
import cStringIO

logging.basicConfig(level=logging.DEBUG)


class Project:
    def __init__(self, filename="tasks.pickle"):

        self.fileName = filename
        if os.path.isfile(self.fileName):
            logging.debug("loading " + self.fileName)
            f = open(self.fileName, 'r+')
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
                    'ch': [],
                    'pid': None  # root task has a special pid
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

        else:
            parent = self.p['t'][pid]
            if parent['ch']:
                peer_id = parent['ch'][-1]

        if pid == task['id']:
            raise Exception("task cannot be it's own parent")
        if not task['id']:
            raise Exception("cannot move root task")
        if tid in [t['id'] for t in self.parents_of(parent)]:
            logging.debug("swap: %d is parent of %d." % (tid, pid))
            # moving task under one of its children:
            # first make new parent our peer
            self.mv_task(tid=pid, peer_id=tid)
            self.list(0)
            # then do the move
            self.mv_task(tid=tid, pid=pid, peer_id=peer_id)
            return

        task['pid'] = pid
        # pop from old parent
        old_parent['ch'].remove(tid)
        if peer_id:
            parent['ch'].insert(peer_id, tid)
        else:
            parent['ch'].append(tid)


    def childrenids(self, tid):
        return self.p['t'][tid]['ch']

    def children(self, tid):
        return self.tasks(self.childrenids(tid))

    def save(self, filename=None):
        if not filename:
            filename = self.fileName
        logging.debug("saving file")
        f = open(filename, 'w')
        pickle.dump(self.p, f)
        f.close()

    def update(self, tid, task):
        if 'id' in task:
            del task['id']  # cannot change the task id
        self.p['t'][tid].update(task)

    def list_pprint_int(self, idlist, seek, indent=""):
        for t in self.tasks(idlist):
            if seek == 0 or seek == t['id']:
                print indent + '{0:04d}'.format(t['id']) + " " + t['m']
                self.list_pprint_int(t['ch'], 0, indent + " ")

    def list_pprint(self, seek):
        print self.p['t'][0]['m']
        self.list_pprint_int(self.childrenids(0), seek, ' ')

    def list_html(self, seek):
        # out = cStringIO.StringIO()
        out = sys.stdout
        print >>out, """<!DOCTYPE html><head><title>"""
        print >>out, self.p['t'][0]['m'].splitlines()[0]
        print >>out, """</title>"""
        print >>out, """
        <style>
body {
    width: 100%; text-align: center;
    font-family:"Tahoma, Geneva, sans-serif"; font-size:large;
    background-color:#202010;
}
#contents {
    text-align: left;
    background-color:LightSteelBlue;
    max-width:900px;
    border: 2px solid black;
    margin: 0px auto;
    padding: 1em;
}
h1   {color:blue}
div.t { margin-left: 1em;}
h1 span, h2 span, h3 span, h4 span, h5 span, h6 span {background-color:LightSlateGray; color:YellowGreen; font-size:medium }
</style>
</head><body><div id="contents">"""
        self.list_html_int(self.childrenids(0), seek, out, 0)
        print >>out, """</div></body></html>"""


    def list_html_int(self, idlist, seek, out, nesting):
        tag = ['h1', 'h2', 'h3', 'h4', 'h6'][nesting if nesting <= 4 else 4 ]

        for t in self.tasks(idlist):
            if seek == 0 or seek == t['id']:
                print >>out, '<{tag}><span>{id:04d}</span> {m} </{tag}><div class="t">'.format(tag=tag, id=t['id'], m=t['m'].split('\n', 1)[0])
                print >>out, '<p>{m}</p>'.format(m='\n'.join(t['m'].split('\n')[1:]).replace('\n','<br />\n'))
                self.list_html_int(t['ch'], 0, out, nesting+1)
                print >>out, "</div>"

    def parents_of(self, task):
        pid = task['pid']
        if not pid:
            return
        while pid:
            task = self.p['t'][pid]
            yield task
            pid = task['pid']
        yield self.p['t'][0]

    @staticmethod
    def diff(left, right):
        result = dict()
        result['+'] = dict([(k, left.p['t'][k]) for k in (set(left.p['t'].keys()) - set(right.p['t'].keys()))])
        result['-'] = set(right.p['t'].keys()) - set(left.p['t'].keys())
        result['>'] = dict()  # edited tasks
        result['^'] = set()  # task that were changed indirectly (their children have changed)

        for (l, r) in [(left.p['t'][k], right.p['t'][k]) for k in set(left.p['t'].keys()) & set(right.p['t'].keys())]:
            td = dict()
            # deadline, owner and state may simply either match or not
            for binKey in set(l.keys()) & set(['d', 'o', 's', 'pid']):
                if binKey not in r or l[binKey] != r[binKey]:
                    td[binKey] = l[binKey]
            differ = difflib.Differ()
            if l['m'] != r['m']:
                td['m'] = list(differ.compare(l['m'], r['m']))
            if l['ch'] != r['ch']:
                td['ch'] = list(differ.compare(l['ch'], r['ch']))

            if td:
                result['>'][l['id']] = td
                result['^'].update(set([t['id'] for t in left.parents_of(l)]))

        result['^'].difference_update(result['>'].keys())  # remove IDs of tasks that have been also edited directly
        return result

    def tree_check(self):
        """
        Traces each nodes path to root
        :return:
        """
        for id, task in self.p['t'].enumerate():
            if id != 0:
                parents = set()
                for parent in self.parents_of(task):
                    if parent['id'] in parents:
                        # a loop in hierarchy
                        return False
                    parents.insert(parent['id'])
                    if parent['id'] == 0:
                        break
            for child in self.children(id):
                if child['pid'] != id:
                    return False
            return True


    def diff_to(self, right):
        return diff(self, right)

    def diff_applies(self, diff):
        """
        Check id a diff applies to this Project
        :param diff:
        :return:
        """
        if set(diff['+'].keys()) & set(self.p['t']).keys():
            # already have some of the tasks that diff attempts to add
            return False
        if set(diff['-'].keys()) & set(self.p['t']).keys() != set(diff['-'].keys()):
            # some tasks that diff attempts to remove are not present
            return False
        if set(diff['>'].keys()) & set(self.p['t']).keys() != set(diff['>'].keys()):
            # some tasks that diff attempts to edit are not present
            return False
        return True

    def apply(self, diff):
        pass

# commands

def start(params):
    logging.info("starting project: " + params.m)
    project = Project()
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
    if params.format == 'pprint':
        project.list_pprint(params.tid)
    elif params.format == 'html':
        project.list_html(params.tid)


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


def diff(params):
    logging.info("computing diff {} - {}: ".format(params.from_file, params.to_file))
    right = Project(params.from_file)
    left = Project(params.to_file)
    result = Project.diff(left, right)
    pprint.pprint(result)


parser = argparse.ArgumentParser(description='simple project TAsk management.')
subparsers = parser.add_subparsers()

subparser = subparsers.add_parser('start', help="start new project")
subparser.add_argument('m', type=unicode, help="project title")
subparser.set_defaults(func=start)

subparser = subparsers.add_parser('ls', help="list project file")
subparser.add_argument('tid', type=int, default=0, nargs='?', help="id of task to print, 0 (whole project) by default")
subparser.add_argument('-f','--format', choices=['pprint', 'html'], default='pprint', nargs='?', help="list format")
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

subparser = subparsers.add_parser('diff', help="print diff between two task lists (e.g. to_file-from_file) ")
subparser.add_argument('from_file', type=unicode, help="right hand file of diff")
subparser.add_argument('to_file', type=unicode, help="left hand file of diff")
subparser.set_defaults(func=diff)

params = parser.parse_args()
logging.debug(str(params))
params.func(params)


