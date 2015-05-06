#!/c/Python27/python.exe
# -*- coding: utf-8 -*-

import pickle
import logging
import os.path
import argparse

logging.basicConfig(level=logging.DEBUG)

c_fname = "tasks.pickle"
proj = {}
pfile = None

def load():
	global pfile
	global proj

	if os.path.isfile(c_fname):
		logging.debug("loading " + c_fname)
		pfile = open(c_fname, 'r+')
		proj = pickle.load(pfile)
	else:
		logging.error("no such file")
		exit()


def save():
	global pfile
	global proj
	
	if pfile:
		logging.debug("saving file")
		pickle.dump(proj, pfile)
	else:
		logging.error("file is None")
		exit()
	
	
def pprint(task, seek, indent):
	if seek==0 or seek==task['id']:
		print indent + '{0:05d}'.format(task['id']) + " " + task['m']
		seek = 0
	for subtask in task['t']:
		pprint(subtask, indent+' ')

# commands

def start(args):
	global pfile
	global proj
	logging.info("starting project: " + args.m)
	pfile = open(c_fname, 'w')
	proj['tid'] = 0;
	proj['t'] = {
		'id' : 0,
		'm' : args.m,
		't' : []
	}
	save()

def add(args):
	global pfile
	global proj
	logging.info("adding task: " + args.m)
	load()
	tid = proj['tid'] + 1
	proj['tid'] = tid;
	proj['t'] = {
		'id' : tid,
		'm' : args.m,
		't' : []
	}
	save()
	
def ls(args):
	global proj
	logging.info("listing task: " + str(args.tid))
	load()
	pprint(proj['t'], args.tid, '')

def edit(args):
	global proj
	logging.info("editing task: " + str(args.tid))

def move(args):
	global proj
	logging.info("moving task: " + str(args.tid))

def remove(args):
	global proj
	logging.info("deleting task: " + str(args.tid))

	
parser = argparse.ArgumentParser(description='simple PROject TAsk management.')
subparsers = parser.add_subparsers()

subparser = subparsers.add_parser('start', help="start new project")
subparser.add_argument('m', type=unicode, help="project title")
subparser.set_defaults(func=start)

subparser = subparsers.add_parser('ls', help="list project file")
subparser.add_argument('tid', type=int, default=0, nargs='?', help="id of task to print, 0 (whole project) by default")
subparser.set_defaults(func=ls)

subparser = subparsers.add_parser('add', help="add new task")
subparser.add_argument('-p', '--new-parent', type=int, help="parent id for new task(s)")
subparser.add_argument('-a', '--after', type=int, help="id of task that will precede new task")
subparser.add_argument('-d', '--deadline', type=unicode, nargs='?', help="deadline")
subparser.add_argument('-o', '--owner', type=unicode, nargs='?', default="", help="owner")
subparser.add_argument('-s', '--state', type=unicode, nargs='?', default="new", help="task state")
subparser.add_argument('m', type=unicode, help="task title")
subparser.set_defaults(func=add)

subparser = subparsers.add_parser('e', help="edit task")
subparser.add_argument('tid', type=int, default=0, help="task id")
subparser.add_argument('-m', type=unicode, help="project title")
subparser.add_argument('-d', '--deadline', type=unicode, nargs='?', help="deadline")
subparser.add_argument('-o', '--owner', type=unicode, nargs='?', help="owner")
subparser.add_argument('-s', '--state', type=unicode, nargs='?', help="owner")
subparser.set_defaults(func=edit)

subparser = subparsers.add_parser('rm', help="remove task")
subparser.add_argument('tid', type=int, default=0, help="id of parent task")
subparser.add_argument('m', type=unicode, help="project title")
subparser.add_argument('-d', '--deadline', type=unicode, nargs='?', help="deadline")
subparser.add_argument('-o', '--owner', type=unicode, nargs='?', help="owner")
subparser.set_defaults(func=remove)

subparser = subparsers.add_parser('mv', help="move task(s)")
subparser.add_argument('trange', type=unicode, default=0, help="task range to move")
subparser.add_argument('-p', '--new-parent', type=int, help="new parent for moved task(s)")
subparser.add_argument('-a', '--after', type=int, help="id of task that will precede task range after move")
subparser.set_defaults(func=move)


args = parser.parse_args()
args.func(args)


