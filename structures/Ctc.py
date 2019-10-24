# -*- coding: utf-8 -*-
"""
Created on Wed Sep  4 02:08:51 2019

@author: AsteriskAmpersand
"""

from collections import OrderedDict
try:
    import mathutils as np
    Matrix = np.Matrix
    from ..common.Cstruct import PyCStruct, FileClass
except:
    import sys
    sys.path.insert(0, r'..\common')
    from Cstruct import PyCStruct, FileClass
    import numpy as np
    Matrix = np.matrix

class Header(PyCStruct):
	fields = OrderedDict([
	("filetype","char[4]"),
	("unknownsConstantIntSet","int[3]"),
	("numARecords","int"),
	("numBRecords","int"),
	("unknownConstantInt","int"),
	("updateTicks","float"),
	("poseSnapping","float"),
	("chainDamping","float"),
	("reactionSpeed","float"),
	("gravityMult","float"),
	("windMultMid","float"),
	("windMultLow","float"),
	("windMultHigh","float"),
	("unknownFloatSet","float[3]"),
	("unknownByteSet","byte[8]"),])
#} header 

class ARecord(PyCStruct):
	fields = OrderedDict([
	("chainLength","int"),
	("collision","byte"),
	("weightiness","byte"),
	("unknownByteSet","byte[26]"),
	("xGravity","float"),
	("yGravity","float"),
	("zGravity","float"),
	("unknownFloatOne","float"),
	("xInertia","float"),
	("yInertia","float"),
	("zInertia","float"),
	("unknownFloatTwo","float"),
	("unknownFloatThree","float"),
	("unknownFloatFour","float"),
	("windMultiplier","float"),
	("lod","int"),])
#} arecord [ header.numARecords ] 
class BRecord(PyCStruct):
    fields = OrderedDict([
	("negXMax","float"),
	("negYMax","float"),
	("negZMax","float"),
	("worldX","float"),
	("zMax","float"),
	("yMax","float"),
	("xMax","float"),
	("worldY","float"),
	("xSomething","float"),
	("ySomething","float"),
	("zSomething","float"),
	("worldZ","float"),
	("unknFloat1","float"),
	("unknFloat2","float"),
	("unknFloat3","float"),
	("unknFloat4","float"),
	("unknownByteSetOne","byte[2]"),
	("isChainParent","byte"),
	("unknownByteSetTwo","byte[5]"),
	("boneFunctionID","int"),
	("unknownByteSetThree","byte[4]"),
	("unknownFloatSet","float[4]"),])
    
    def marshall(self, data):
        super().marshall(data)
        self.Matrix = Matrix(        
        [[self.negXMax, self.negYMax, self.negZMax, self.worldX],
        [self.zMax,self.yMax,self.xMax,self.worldY],
        [self.xSomething,self.ySomething,self.zSomething,self.worldZ],
        [self.unknFloat1,self.unknFloat2,self.unknFloat3,self.unknFloat4]]).transpose()
        return self
        
#} brecord [ header.numBRecords ] }}
    
class CtcChain():
    def __init__(self,arecord,brecords):
        self.chain = arecord
        self.nodes = [next(brecords) for _ in range(arecord.chainLength)]
        
    def __len__(self):
        return len(self.nodes)
    
    def __iter__(self):
        return iter(self.nodes)
    
class Ctc():
    def marshall(self,data):
        self.Header = Header().marshall(data)
        arecords = [ARecord().marshall(data) for _ in range(self.Header.numARecords)]
        brecords = [BRecord().marshall(data) for _ in range(self.Header.numBRecords)]
        biter = iter(brecords)
        self.Chains = [CtcChain(chain,biter) for chain in arecords]
        return self
    def __iter__(self):
        return iter(self.Chains)
CtcFile = FileClass(Ctc)


from pathlib import Path
if __name__ == "__main__":
    for ctcf in Path(r"E:\MHW\Merged").rglob("*.ctc"):
        ctc = CtcFile(ctcf).data
        for chain in ctc:
            for node in chain:
                #print(node.Matrix)
                print(node.Matrix[3])