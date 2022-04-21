"""
dinit.DictInit
 Class for Cbject initialization from dictionaries. 

 Caveat with this approach is that update only does a shallow copy of key-value pairs from memberDict.
 Any nonliteral values will not be deep copied.  But this should not be an issue for structures read from a json file.

Example Usage:
----------
import dinit

class MZPeak(dinit.DictInit):
	_requiredMembers = [ "intensity", "mass" ] + dinit.DictInit._requiredMembers


jsonObject =   {
    "intensity" : 0.000244843697874677,
    "mass" : 753.740285012633
  }

# object creation with member validation  
peak = MZPeak.fromDict(jsonObject)

# object creation without member validation
peak = MZPeak(jsonObject)
--------

"""
#
#   Written by Hunter Moseley, 06/18/2014
#   Copyright Hunter Moseley, 06/18/2014. All rights reserved.   
#
__all__ = ('DictInit')
__version__ = '0.1'


class DictInit(object):
	def __init__(self, memberDict):
		self.__dict__.update(memberDict)
	
	@classmethod
	def fromDict(cls, memberDict):
		if cls.isValidDict(memberDict):
			return cls(memberDict)
		else:
			return None
	
	_requiredMembers = [ ]
	
	@classmethod
	def isValidDict(cls, memberDict):
		for required in cls._requiredMembers :
			if not required in memberDict :
				return False
		
		# restrictive testing
		# for contains in memberDict.keys() :
		#	if not contains in cls._requiredMembers :
		#		return False
		
		return True

