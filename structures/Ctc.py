# -*- coding: utf-8 -*-
"""
Created on Wed Sep  4 02:08:51 2019

@author: AsteriskAmpersand
"""

from collections import OrderedDict
try:
    import mathutils as np
    Matrix = np.Matrix
    Vector = np.Vector
    from ..common.Cstruct import PyCStruct, FileClass
except:
    import sys
    sys.path.insert(0, r'..\common')
    from Cstruct import PyCStruct, FileClass
    import numpy as np
    Matrix = np.matrix
    Vector = lambda x: np.matrix(x).transpose()

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
	("fixedBytes","byte[8]"),])#1 1 1 1 1 1 0 0
    
    def construct(self,data):
        data["filetype"]="CTC\x00"
        data["fixedBytes"]=[1,1,1,1,1,1,0,0]
        super().construct(data)
        return self
#} header 

class ARecord(PyCStruct):
    fields = OrderedDict([
	("chainLength","int"),
	("collision","byte"),
	("weightiness","byte"),
	("unknownByteSet","byte[2]"),
    ("fixedNegativeOne","byte[4]"),
    ("oneZeroZeroZero1","byte[4]"),
    ("oneZeroZeroZero2","byte[4]"),
    ("unknownByteSetCont","byte[12]"),
	("xGravity","float"),
	("yGravity","float"),
	("zGravity","float"),
	("zeroFloat","float"),
	("snapping","float"),
	("coneLimit","float"),
	("tension","float"),
	("unknownFloatTwo","float"),#100
	("unknownFloatThree","float"),#0
	("unknownFloatFour","float"),#0.1
	("windMultiplier","float"),
	("lod","int"),])
    
    def construct(self,data):
        data["fixedNegativeOne"] = [-1]*4
        data["oneZeroZeroZero1"] = [1,0,0,0]
        data["oneZeroZeroZero2"] = [1,0,0,0]
        data["zeroFloat"] = 0.0
        super().construct(data)
        return self
    
    renameScheme = {
            	"chainLength":"Chain Length",
            	"collision":"CCL Collision",
            	"weightiness":"Weightiness",
            	"xGravity":"X-Axis Gravity",
            	"yGravity":"Y-Axis Gravity",
            	"zGravity":"Z-Axis Gravity",
            	"snapping":"Snapping",
            	"coneLimit":"Cone of Motion",
            	"tension":"Tension",
            	"windMultiplier":"Wind Multiplier",
            	"lod":"Level of Detail",
            	"unknownFloatTwo":"{Unknown Float 00}",#100 Normally
            	"unknownFloatThree":"{Unknown Float 01}",#0 Normally
            	"unknownFloatFour":"{Unknown Float 02}"#0.1 Normally
            }
    
#} arecord [ header.numARecords ] 
class BRecord(PyCStruct):
    fields = OrderedDict([
	("m00","float"),
	("m10","float"),
	("m20","float"),
	("m30","float"),
	("m01","float"),
	("m11","float"),
	("m21","float"),
	("m31","float"),
	("m02","float"),
	("m12","float"),
	("m22","float"),
	("m32","float"),
	("m03","float"),
	("m13","float"),
	("m23","float"),
	("m33","float"),
	("zeroSet1","byte[2]"),#0/54,0
	("isChainParent","byte"),
	("unknownByteSetTwo","ubyte[5]"),
	("boneFunctionID","int"),
	("zeroSet3","byte[4]"),
    ("radius","float"),
    ("unknownFloatSet","float[2]"),
    ("oneFloat","float[2]"),#FLOAT,1
    ("unknownExtendedByteSet","byte[12]")#-51 all the way
    ])
    
    def marshall(self, data):
        super().marshall(data)
        self.Matrix = Matrix(        
        [[self.m00, self.m01, self.m02, self.m03],
         [self.m10, self.m11, self.m12, self.m13],
         [self.m20, self.m21, self.m22, self.m23],
         [self.m30, self.m31, self.m23, self.m33],
         ])
        return self
    
    def construct(self, data):
        for i,j in [(i,j) for i in range(4) for j in range(4)]:
            data["m%d%d"%(i,j)] = data["Matrix"][i][j]
        data["zeroSet1"] = [0,0]
        data["zeroSet3"] = [0,0,0,0] 
        data["oneFloat"] = [1.0,1.0]
        data["unknownExtendedByteSet"] = [-51]*12
        super().construct(data)
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
        self.arecords = [ARecord().marshall(data) for _ in range(self.Header.numARecords)]
        self.brecords = [BRecord().marshall(data) for _ in range(self.Header.numBRecords)]
        biter = iter(self.brecords)
        self.Chains = [CtcChain(chain,biter) for chain in self.arecords]
        return self
    def construct(self,header,chains,nodes):
        self.Header = header
        self.arecords = chains
        self.brecords = nodes
        return self
    def serialize(self):
        return self.Header.serialize()+ \
                    b''.join([arecord.serialize() for arecord in self.arecords])+ \
                    b''.join([brecord.serialize() for brecord in self.brecords])
    def __iter__(self):
        return iter(self.Chains)
CtcFile = FileClass(Ctc)

if __name__ == "__main__":
    from pathlib import Path
    checks = {"fixedBytes":set()}
    acheck = {"unknownFloatTwo":set(),"unknownFloatThree":set(),"unknownFloatFour":set(),
              "unknownByteSet":set(),"fixedNegativeOne":set(),"oneZeroZeroZero1":set(),
              "oneZeroZeroZero2":set(),"coneLimit":set()}
    bcheck = {"unknownFloatSet":set(),
              "m03":set(),"m13":set(),"m23":set(),"m33":set(),
            "zeroSet1":set(),"zeroSet3":set(),"oneFloat":set(),"unknownExtendedByteSet":set()}
    def norm(v):
        return np.sqrt(v[0]**2+v[1]**2+v[2]**2)

    def ifAdd(dictionary, key, data):
        if key in dictionary:
            dictionary[key].append(data)
        else:
            dictionary[key]=[data]
        return dictionary
    def tryTuple(obj):
        try:
            return tuple(obj)
        except:
            return obj
    for ctcf in Path(r"E:\MHW\ChunkG0").rglob("*.ctc"):
        ctc = CtcFile(ctcf).data
        for c in checks:
            checks[c].add(tryTuple(getattr(ctc.Header,c)))
        for chain in ctc:
            c = chain.chain
            for a in acheck:
                acheck[a].add(tryTuple(getattr(c,a)))
            for node in chain:
                for b in bcheck:
                    bcheck[b].add(tryTuple(getattr(node,b)))
    for c in checks:
        print(c)
        print(checks[c])
    for c in acheck:
        print(c)
        print(acheck[c])
    for c in bcheck:
        print(c)
        print(bcheck[c])
    """
    uci = set()
    ui = set()
    ufs = [set() for _ in range(3)]
    ubs = [set() for _ in range(8)]
    
    ws = [set() for i in range(2)]
    ws2 = [set() for i in range(12)]
    centi = {}
    zero = {}
    uno = {}
    
        uci.add(tuple(ctc.Header.unknownsConstantIntSet))
        ui.add(ctc.Header.unknownConstantInt)
        for v,s in zip(ctc.Header.unknownFloatSet,ufs):
            s.add(v)
        for v,s in zip(ctc.Header.unknownByteSet,ubs):
            s.add(v)
            ifAdd(centi, chain.chain.unknownFloatTwo, ctcf.relative_to("E:\MHW\Merged").as_posix())
            ifAdd(zero, chain.chain.unknownFloatThree, ctcf.relative_to("E:\MHW\Merged").as_posix())
            ifAdd(uno, chain.chain.unknownFloatFour, ctcf.relative_to("E:\MHW\Merged").as_posix())
            for byte, container in zip(chain.chain.unknownByteSet,ws):
                container.add(byte)
            for byte, container in zip(chain.chain.unknownByteSetCont,ws2):
                container.add(byte)   
    outputroot = Path(r"G:\Wisdom\DataOutputs")
    with outputroot.joinpath("centi.csv").open("w") as fil:
        json.dump(centi,fil)
    with outputroot.joinpath("zero.csv").open("w") as fil:
        json.dump(zero,fil)
    with outputroot.joinpath("uno.csv").open("w") as fil:
        json.dump(uno,fil)
    for entry in ws:
        print(entry)
    for entry in ws2:
        print(entry)
    print(uci)
    print(ui)
    print(ufs)
    print(ubs)
    """