#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright 2017, 2018, Kevin Laeufer <laeufer@eecs.berkeley.edu>

# This software may be modified and distributed under the terms
# of the BSD license. See the LICENSE file for details.

import util.typed as typed
from enum import Enum
from typing import List

class DebugInfo:
	def __init__(self, file="", line=-1, col=-1):
		self.file = file
		self.line = line
		self.col = col


class Node(typed.Node):
	name = typed.Optional(str)
	dbg = typed.Optional(DebugInfo)

################################################################################

class Channel(Node):
	width = int

################################################################################
class Condition(Node):
	pass
class High(Condition):
	channel = Channel
class Low(Condition):
	channel = Channel
class ConstantCondition(Condition):
	value = bool
class Bop(Enum):
	And = 0
class ConditionBinOp(Condition):
	op = Bop
	left = Condition
	right = Condition

# Important note about events
# ---------------------------
# We ensure that events only have a single source event by prohibiting
# dependencies on multiple events.
# The only places where a list of events is acceptable are for events
# that change states (e.g. change DFA state or shift register content)
# or for the list of outputs.
# The `emit` event of a Register needs to be unique since it will directly
# cause another event in the same cycle.

class Event(Node):
	pass

class Edge(Enum):
	Rising = 0
	Falling = 1

class ExternalEvent(Event):
	edge = Edge
	channel = Channel

class DelayedEvent(Event):
	cycles = int

class InternalEvent(Event):
	trigger = Event
	guard = typed.Optional(Condition)

# data carrying event
class Sample(Event):
	trigger = Event
	channel = Channel

################################################################################
class Token(Node):
	width = int
	has_duration = bool

class Action(Node):
	token = Token

class Start(Action): pass
class Append(Action):
	# TODO: allow to append Token instead of sampling from a channel!
	channel = Channel
class Emit(Action): pass
class Reset(Action): pass

################################################################################
class State(Node):
	pass

class Transition(Event):
	source = State
	destination = State
	trigger = Event
	actions = List[Action]


class DFA(Node):
	start = State
	states = List[State]	# start and end state(s) need to be included!
	transitions = List[Transition]

################################################################################

class Decoder(Node):
	inputs = List[Channel]
	outputs = List[Token]
	dfas = List[DFA]

################################################################################
