#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright 2017, 2018, Kevin Laeufer <laeufer@eecs.berkeley.edu>

# This software may be modified and distributed under the terms
# of the BSD license. See the LICENSE file for details.

# some midend passes

import ast, re
import util.typed as typed
import util.meta as meta
import midend.ir as ir
from typing import List, Set

class StateInfoPass(ast.NodeVisitor):
	# tags transitions with their source state
	def __init__(self, start_node):
		self.outgoing = meta.MetaDataField('outgoing', ir.State, List[ir.Transition], readonly=False)
		self.incoming = meta.MetaDataField('incoming', ir.State, List[ir.Transition], readonly=False)
		self.dfa      = meta.MetaDataField('dfa', ir.State, ir.DFA, readonly=False)
		self.visit(start_node)
		self.outgoing.readonly = True
		self.incoming.readonly = True
		self.dfa.readonly = True
	def visit_Decoder(self, node):
		for dfa in node.dfas:
			self.visit(dfa)
	def visit_DFA(self, node):
		for tran in node.transitions:
			self.visit(tran)
		assert node.start in node.states
		for state in node.states:
			self.dfa.set(state, node)
	def visit_Transition(self, node):
		self.outgoing.add(node.source, node)
		self.incoming.add(node.destination, node)

def filter_none(ll): return [ee for ee in ll if ee is not None]

class DeadCodeEliminationPass(ast.NodeVisitor):
	# Remove all actions that reference tokens that are not outpus.
	# Remove all dfas that do not contain any actions.
	# Remove all inputs that are not used any action.
	# Keep all inputs that trigger transitions.
	def __init__(self, decoder, state=None):
		assert isinstance(decoder, ir.Decoder)
		if state is None: state = StateInfoPass(decoder)
		assert isinstance(state, StateInfoPass)
		self.state = state
		#
		self.used_tokens = set(decoder.outputs)
		self.used_inputs = set()
		used_dfas = filter_none([self.visit(dfa) for dfa in decoder.dfas])
		# keep triggers
		for dfa in used_dfas:
			for tran in dfa.transitions:
				self.visit(tran.trigger)
		self.decoder = decoder.set(inputs=list(self.used_inputs),
		                           dfas=used_dfas)
	def visit_DFA(self, dfa):
		transitions = [self.visit(tran) for tran in dfa.transitions]
		action_count = sum(len(tran.actions) for tran in transitions)
		if action_count > 0:
			return dfa.set(transitions=transitions)
	def visit_Transition(self, tran):
		return tran.set(actions=filter_none(self.visit(action) for action in tran.actions))
	def visit_Append(self, append):
		if append.token in self.used_tokens:
			self.used_inputs.add(append.channel)
			return append
	def visit_Start(self, action):
		if action.token in self.used_tokens:
			return action
	def visit_Emit(self, action):
		if action.token in self.used_tokens:
			return action
	def visit_Reset(self, action):
		if action.token in self.used_tokens:
			return action
	def visit_InternalEvent(self, event):
		self.visit(event.guard)
		self.visit(event.trigger)
	def visit_ExternalEvent(self, event):
		self.used_inputs.add(event.channel)
	def visit_Low(self, condition):
		self.used_inputs.add(condition.channel)
	def visit_High(self, condition):
		self.used_inputs.add(condition.channel)
	def visit_NoneType(self, none): pass
	def generic_visit(self, node):
		raise NotImplementedError("TODO: handle nodes of type {}".format(type(node)))
