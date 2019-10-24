# -*- coding: utf-8 -*-
"""
Created on Wed Sep  4 02:54:42 2019

@author: AsteriskAmpersand
"""

from pathlib import Path
from structures.Ccl import CclFile

tickValues = set()
unkF1 = set()
unkF2 = set()
unkF3 = set()
unkF4 = set()
unknownLimit4 = set()

for path in Path(r"E:\MHW\Merged").rglob("*.ctc"):
    ctcF = CtcFile(path)
    tickValues.add(ctcF.data.Header.updateTicks)
    for record in ctcF.data.Chains:
        unkF1.add(record.chain.unknownFloatOne)
        unkF2.add(record.chain.unknownFloatTwo)
        unkF3.add(record.chain.unknownFloatThree)
        unkF4.add(record.chain.unknownFloatFour)
        for boneRecord in record.nodes:
            unknownLimit4.add(boneRecord.unknFloat4)

print(tickValues)
print(unkF1)
print(unkF2)
print(unkF3)
print(unkF4)
print(unknownLimit4)