"""
copier.Copier
  Class of objects designed to copy values during intermediate execution like if statements
  
Example Usage:
------------
import copier
import re

reCopier = copier.Copier()
if reCopier(re.match('\w+',a_string)) :
	match = reCopier.value  # or reCopier.get()
	...
------------

copier.Accumulator
  Class of objects designed to accumulate values during intermediate execution
  
Exmaple Usage:
------------
import copier

accum = copier.Accumulator()

for x in something :
	if accum(x == 5) :
		...
	elif accum(x > 25) :
		...

results  = accum.value  # or accum.get()
------------
"""
#
#   Written by Hunter Moseley, 06/18/2014
#   Copyright Hunter Moseley, 06/18/2014. All rights reserved.   
#

__all__ = ('Copier', 'Accumulator')
__version__ = '0.1'


class Copier(object):
	def __init__(self, value=None):
		self.value = value
		
	def __call__(self, value):
		return self.set(value)
		
	def set(self, value):
		self.value = value
		return value
		
	def get(self):
		return self.value

class Accumulator(Copier):
	def __init__(self):
		self.value = []
	
	def __call__(self, value):
		return self.add(value)
		
	def add(self, value):
		self.value.append(value)
		return value
