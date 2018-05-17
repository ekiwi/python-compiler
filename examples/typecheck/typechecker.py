#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright 2017, 2018, Kevin Laeufer <laeufer@eecs.berkeley.edu>

# This software may be modified and distributed under the terms
# of the BSD license. See the LICENSE file for details.

import ast
import astor
import irtypes as ir

def ensure_float(node):
	if node.type == ir.Type.Float: return node
	else: return ir.CastToFloat(expr=node, type=ir.Type.Float)

def ensure_int(node):
	if node.type == ir.Type.Int: return node
	else: return ir.CastToInt(expr=node, type=ir.Type.Int)

def ensure_bool(node):
	if node.type == ir.Type.Bool: return node
	else: return ir.CastToBool(expr=node, type=ir.Type.Bool)

class TypeChecker(ast.NodeVisitor):
	@staticmethod
	def analyze(ir_code):
		tc = TypeChecker()
		type_checked_ast = tc.visit(ir_code)
		return (type_checked_ast, tc.symbols)

	# Your code here...

	def __init__(self):
		super(TypeChecker, self).__init__()
		self.return_type = None
		self.symbols = {}

	def _declare_sym(self, name, tt):
		assert isinstance(name, str)
		assert isinstance(tt, ir.Type)
		if tt != self.symbols.get(name, tt):
			raise TypeError("Cannot redeclare reference `{}` ({}) with different type `{}`)".format(
				name, self.symbols[name], tt))
		self.symbols[name] = tt

	def visit_BinOp(self, node):
		promote_bool_to_int = (ir.Bop.Add, ir.Bop.Sub, ir.Bop.Mul, ir.Bop.Div, ir.Bop.Mod)
		left = self.visit(node.left)
		right = self.visit(node.right)
		if left.type == right.type:
			if left.type == ir.Type.Bool and node.op in promote_bool_to_int:
				return node.set(left=ensure_int(left), right=ensure_int(right), type=ir.Type.Int)
			else:
				return node.set(left=left, right=right, type=left.type)
		else:
			types = (left.type, right.type)
			if ir.Type.Float in types:
				return node.set(left=ensure_float(left), right=ensure_float(right), type=ir.Type.Float)
			elif ir.Type.Int in types:
				return node.set(left=ensure_int(left), right=ensure_int(right), type=ir.Type.Int)
			else:
				assert False, "should never get here!"

	def visit_CmpOp(self, node):
		left = self.visit(node.left)
		right = self.visit(node.right)
		if left.type == right.type:
			return node.set(left=left, right=right, type=ir.Type.Bool)
		else:
			types = (left.type, right.type)
			if ir.Type.Float in types:
				return node.set(left=ensure_float(left), right=ensure_float(right), type=ir.Type.Bool)
			elif ir.Type.Int in types:
				return node.set(left=ensure_int(left), right=ensure_int(right), type=ir.Type.Bool)
			else:
				assert False, "should never get here!"

	def visit_UnOp(self, node):
		e = self.visit(node.e)
		if node.op == ir.Uop.Neg:
			e = ensure_int(e) if e.type == ir.Type.Bool else e
		else:
			e = ensure_bool(e)
		return node.set(e=e, type=e.type)

	def _check_index(self, ref):
		assert isinstance(ref, ir.Ref)
		if ref.index is None: return None
		index = self.visit(ref.index)
		if index.type != ir.Type.Int:
			raise TypeError("array indices must be 'Int', not '{}'".format(index.type))
		return index

	def visit_Ref(self, node):
		if node.name not in self.symbols:
			raise NameError("name '{}' is not defined".format(node.name))
		tt = self.symbols[node.name]
		index = self._check_index(node)
		has_index = index is not None
		if has_index and not tt.is_array():
			raise TypeError("'{}' object is not subscriptable".format(tt))
		if has_index: tt = tt.to_scalar()
		return node.set(type=tt, index=index)

	def visit_IntConst(self, node):
		return node.set(type=ir.Type.Int)
	def visit_FloatConst(self, node):
		return node.set(type=ir.Type.Float)
	def visit_BoolConst(self, node):
		return node.set(type=ir.Type.Bool)
	def visit_VoidConst(self, node):
		return node.set(type=ir.Type.Void)
	def visit_CastToFloat(self, node):
		expr = self.visit(node.expr)
		if expr.type == ir.Type.Float:
			return expr
		return ir.CastToFloat(expr=expr, type=ir.Type.Float)
	def visit_CastToInt(self, node):
		expr = self.visit(node.expr)
		if expr.type == ir.Type.Int:
			return expr
		return ir.CastToInt(expr=expr, type=ir.Type.Int)
	def visit_CastToBool(self, node):
		expr = self.visit(node.expr)
		if expr.type == ir.Type.Bool:
			return expr
		return ir.CastToBool(expr=expr, type=ir.Type.Bool)

	def visit_Assign(self, node):
		val = self.visit(node.val)
		if val.type.is_array():
			raise TypeError("cannot assign arrays!")
		index = self._check_index(node.ref)
		tt = val.type if index is None else val.type.to_array()
		self._declare_sym(node.ref.name, tt)
		return ir.Assign(ref=node.ref.set(type=tt, index=index), val=val)

	def visit_For(self, node):
		start = self.visit(node.min)
		if start.type != ir.Type.Int:
			raise TypeError("Lower loop bound need to be of type 'Int', not '{}'".format(start.type))
		stop = self.visit(node.max)
		if stop.type != ir.Type.Int:
			raise TypeError("Upper loop bound need to be of type 'Int', not '{}'".format(stop.type))
		self._declare_sym(node.var, ir.Type.Int)
		return node.set(min=start, max=stop, body=self.visit(node.body))

	def visit_Return(self, node):
		val = self.visit(node.val)
		if self.return_type != val.type:
			raise TypeError('Cannot return {} as {}'.format(val.type, self.return_type))
		return ir.Return(val=val, type=val.type)

	def visit_FuncDef(self, node):
		self.return_type = node.return_type
		for name, tt in zip(node.args, node.arg_types):
			self._declare_sym(name, tt)
		typed_fun = node.map(self.visit, [ir.Stmt])
		# TODO: if the return type is not None, make sure that there is no fall through
		return typed_fun

	def generic_visit(self, node):
		# TODO: remove eventually!
		return node.map(self.visit, [ir.Stmt, ir.Expr])
