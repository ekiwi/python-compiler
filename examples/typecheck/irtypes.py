#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright 2017, 2018, Kevin Laeufer <laeufer@eecs.berkeley.edu>

# This software may be modified and distributed under the terms
# of the BSD license. See the LICENSE file for details.


import typed as kast
from typing import List
from enum import Enum
import ast

class Uop(Enum):
	Neg = 0
	Not = 1
class Bop(Enum):
	Add = 0
	Sub = 1
	Mul = 2
	Div = 3
	Mod = 4
	And = 5
	Or = 6
class Cop(Enum):
	EQ = 0
	NE = 1
	LT = 2
	GT = 3
	LE = 4
	GE = 5

class Type(Enum):
	Int = 0
	IntArray = 1
	Float = 2
	FloatArray = 3
	Bool = 4
	BoolArray = 5
	Void = 6
	def is_array(self):
		return self.name.endswith("Array")
	def to_array(self):
		if self.is_array(): return self
		if self == Type.Void: assert False, "no void arrays!"
		return { Type.Int:   Type.IntArray,
		         Type.Float: Type.FloatArray,
		         Type.Bool:  Type.BoolArray}[self]
	def to_scalar(self):
		if not self.is_array(): return self
		return { Type.IntArray:   Type.Int,
		         Type.FloatArray: Type.Float,
		         Type.BoolArray:  Type.Bool}[self]

## Exprs ##
class Expr(kast.AST):
	# the type of an expression will be determined by the Type"Checker"
	type = kast.Optional(Type)

class BinOp(Expr):
	op = Bop
	left = Expr
	right = Expr

class CmpOp(Expr):
	op = Cop
	left = Expr
	right = Expr

class UnOp(Expr):
	op = Uop
	e = Expr

class Ref(Expr):
	name = str
	index = kast.Optional(Expr)

class IntConst(Expr):
	val = int

class FloatConst(Expr):
	val = float

class BoolConst(Expr):
	val = bool

class VoidConst(Expr):
	pass

class CastToFloat(Expr):
	expr = Expr

class CastToInt(Expr):
	expr = Expr

class CastToBool(Expr):
	expr = Expr

## Stmts ##
class Stmt(kast.AST):
	pass

class Assign(Stmt):
	ref = Ref
	val = Expr

class Block(Stmt):
	body = List[Stmt]

class If(Stmt):
	cond = Expr
	body = Stmt
	elseBody = kast.Optional(Stmt)

class For(Stmt):
	var = str
	min = Expr
	max = Expr
	body = Stmt

class Return(Stmt, Expr):
	val = Expr

class FuncDef(Stmt):
	name = str
	args = List[str]
	body = Stmt
	arg_types = List[Type]
	return_type = Type

