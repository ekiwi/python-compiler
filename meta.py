#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright 2017, 2018, Kevin Laeufer <laeufer@eecs.berkeley.edu>

# This software may be modified and distributed under the terms
# of the BSD license. See the LICENSE file for details.


import util.typed as typed
from util.typed import _typing_aware_isinstance

class MetaDataField:
	def __init__(self, name, defined_on, entry_type, readonly=True):
		self.name = name
		self.entry_type = entry_type
		self.defined_on = defined_on
		self.readonly = readonly
		# check invariances
		assert issubclass(self.defined_on, typed.Node)
		# dynamic data
		self.entries = {}

	def _check_node_type(self, node):
		if not _typing_aware_isinstance(node, self.defined_on):
			raise TypeError("{} not defined on nodes of type {}".format(self.name, type(node)))
	def _check_writable(self):
		if self.readonly:
			raise RuntimeError("trying to write readonly metadata {}".format(self.name))
	def _check_value_type(self, value):
		if not _typing_aware_isinstance(value, self.entry_type):
			raise TypeError("{} needs to be of type {} not {}".format(self.name, self.entry_type, type(value)))
	def _check_is_list(self):
		if not typed._is_list_type(self.entry_type):
			raise TypeError("entry type {} of {} is not a list".format(self.entry_type, self.name))
	def _check_list_entry_type(self, value):
		self._check_is_list()
		inner = typed._get_list_element_type(self.entry_type)
		if not _typing_aware_isinstance(value, inner):
			raise TypeError("{} needs to be of type {} not {}".format(self.name, inner, type(value)))

	def set(self, node, value):
		self._check_node_type(node)
		self._check_value_type(value)
		self._check_writable()
		self.entries[node] = value
		return value

	def get(self, node):
		self._check_node_type(node)
		if not node in self.entries:
			if typed._is_list_type(self.entry_type):
				return []
			raise KeyError("{} not set on node {}".format(self.name, node))
		return self.entries[node]

	def add(self, node, value):
		self._check_node_type(node)
		self._check_list_entry_type(value)
		self._check_writable()
		if node not in self.entries:
			self.entries[node] = []
		self.entries[node].append(value)

class MetaDataProxy:
	# the `.meta` object of typed.Node
	def __init__(self, node, repo):
		self.node = node
		self.repo = repo
		# check invariances
		assert isinstance(self.node, typed.Node)
		assert isinstance(self.repo, MetaRepository)
	def update_repo(self):
		self.repo = repo
		assert isinstance(self.repo, MetaRepository)
	def __setattr__(self, name, value):
		self.repo.get_field(name).set(self, value)
	def __getattr__(self, name):
		self.repo.get_field(name).get(self)


class MetaRepository:
	# keeps track of metadata
	def __init__(self):
		self.fields = {}
	def add_field(self, field):
		assert isinstance(field, MetaDataField)
		if field.name in self.fields:
			raise RuntimeError("field {} already defined".format(field.name))
		self.fields[field.name] = field
	def get_field(self, name):
		if name not in self.fields:
			raise KeyError("undefined metadata field {}".format(name))
		return self.fields[name]

def to_list(value):
	if isinstance(value, list): return value
	if isinstance(value, tuple): return list(value)
	return [value]
def to_set(value):
	return set(to_list(value))

