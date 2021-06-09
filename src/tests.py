import unittest
import pandas as pd
import numpy as np
import collections as col
import copy

import utils as u
import rule_set as rs
from relation import *
from connection import *


class TestUtilsMethods(unittest.TestCase):

    def test_parse_interval(self):
        #good examples
        inter1 = "(0.8,4.2)" #neither
        inter2 = "(1.8, inf]" #right
        inter3 = "]0,2]" #right
        inter4 = "]0.8, inf[" #open
        inter5 = "(-0.325,0[" #open
        inter6 = "[-inf, -4.2]" #both
        inter7 = "(-inf,inf)" #neither
        inter8 = "]448,448.2)" #neither

        self.assertEqual(u.parse_interval(inter1), pd.Interval(0.8, 4.2, 'neither'))
        self.assertEqual(u.parse_interval(inter2), pd.Interval(1.8, float('inf'), 'right'))
        self.assertEqual(u.parse_interval(inter3), pd.Interval(0,2,'right'))
        self.assertEqual(u.parse_interval(inter4), pd.Interval(0.8, float('inf'), 'neither'))
        self.assertEqual(u.parse_interval(inter5), pd.Interval(-0.325, 0, 'neither'))
        self.assertEqual(u.parse_interval(inter6), pd.Interval(float('-inf'), -4.2, 'both'))
        self.assertEqual(u.parse_interval(inter7), pd.Interval(float('-inf'), float('inf'), 'neither'))
        self.assertEqual(u.parse_interval(inter8), pd.Interval(448, 448.2, 'neither'))

    def test_parse_csv_mini(self):
        ''' Check if parse_cv() produces a list a of rules that gives an equivalent DataFrame when given as argument when initializing a RuleSet (order of the columns is ignored)'''
        #reference ruleset
        r1 = {'AvgNightCons':pd.Interval(150.0,200.0, 'neither'),'InCommunity':False, 'Rec':'rec1'}
        r2 = {'AvgDayCons':pd.Interval(30.0,100.0), 'Rec':'rec2'}
        r3 = {'AvgDayCons':pd.Interval(30.0,120.0),'AvgNightCons':pd.Interval(50.0,150.0),'InCommunity':False, 'Rec':'rec2'}
        rules = [r1, r2, r3]
        ref = rs.RuleSet(rules)
        #tested ruleset
        csv_name = "data/RuleSetMini.csv"
        parsed = u.parse_csv(csv_name)
        checked = rs.RuleSet(parsed)
        self.assertTrue(checked.set.sort_index(axis=1).equals(ref.set.sort_index(axis=1)))

    def test_parse_csv_small(self):
        ''' Check if parse_cv() produces a list a of rules that gives an equivalent DataFrame when given as argument when initializing a RuleSet (order of the columns is ignored)'''
        #reference ruleset
        r1 = col.OrderedDict({'Recommendation': 'Rec1', 'A': pd.Interval(0.0,50.0, 'both'), 'B':pd.Interval(60.0,100.0, 'both'), 'E': False})
        r2 = col.OrderedDict({'Recommendation': 'Rec2', 'A': pd.Interval(0.0,50.0, 'both'), 'E': True})
        r3 = col.OrderedDict({'Recommendation': 'Rec3', 'A': pd.Interval(0.0,50.0, 'both'), 'E':False})
        r4 = col.OrderedDict({'Recommendation': 'Rec4', 'A': float('nan'), 'C':pd.Interval(30.0,70.0, 'both')})
        r5 = col.OrderedDict({'Recommendation': 'Rec1', 'A': pd.Interval(10.0,30.0, 'both'), 'D':pd.Interval(10.0,30.0, 'both'), 'E':False})
        r6 = col.OrderedDict({'Recommendation': 'Rec4', 'C':pd.Interval(30.0,70.0, 'both')})
        r7 = col.OrderedDict({'Recommendation': 'Rec2', 'A':pd.Interval(30.0,60.0, 'both'), 'D':pd.Interval(70.0,120.0, 'both'), 'E':False})
        r8 = col.OrderedDict({'Recommendation': 'Rec3', 'A':pd.Interval(30.0,70.0, 'both'), 'B':pd.Interval(60.0,100.0, 'both'), 'E':False})
        r9 = col.OrderedDict({'Recommendation': 'Rec4', 'C':pd.Interval(70.0,90.0, 'both')})
        rules = [r1, r2, r3, r4, r5, r6, r7, r8, r9]
        ref = rs.RuleSet(rules)
        #tested ruleset
        csv_name = "data/RuleSetSmall.csv"
        parsed = u.parse_csv(csv_name)
        checked = rs.RuleSet(parsed)
        #print(ref.set.sort_index(axis=1))
        #print(checked.set.sort_index(axis=1))
        self.assertTrue(checked.set.sort_index(axis=1).equals(ref.set.sort_index(axis=1)))

class TestMiniSet(unittest.TestCase):
    def setUp(self):
        self.csv_name = "data/RuleSetMini.csv"
        self.rules = u.parse_csv(self.csv_name)
        self.ruleset = rs.RuleSet(self.rules)

    def test_init(self):
        self.assertEqual(self.ruleset.m,len(self.rules[0]))
        self.assertEqual(self.ruleset.n,len(self.rules))
        self.assertEqual(len(self.ruleset.idm),0)
        self.assertEqual(len(self.ruleset.pm),0)
        self.assertEqual(self.ruleset.attr_names,['Rec', 'AvgDayCons', 'AvgNightCons', 'InCommunity'])
        self.assertEqual(type(self.ruleset.attr_names),list)

    def test_build_IDM_PM(self):
        a = 4; b = 3; c = 3
        ref_IDM = np.zeros((a,b,c))
        ref_IDM[0,0,1] = -1; ref_IDM[0,0,2] = -1; ref_IDM[0,1,2] = 1 #Rec
        ref_IDM[1,0,1] = Relation.INCLUSION_JI.value; ref_IDM[1,0,2] = Relation.INCLUSION_JI.value; ref_IDM[1,1,2] = Relation.INCLUSION_IJ.value #AvgDayCons
        ref_IDM[2,0,1] = Relation.INCLUSION_IJ.value; ref_IDM[2,0,2] = Relation.DIFFERENCE.value; ref_IDM[2,1,2] = Relation.INCLUSION_JI.value #AvgNightCons
        ref_IDM[3,0,1] = Relation.INCLUSION_IJ.value; ref_IDM[3,0,2] = Relation.EQUALITY.value; ref_IDM[3,1,2] = Relation.INCLUSION_JI.value #InCommunity
        ref_PM = np.zeros((b,c))
        ref_PM[0,1] = -12; ref_PM[1,2] = 18
        #print("---ref idm original ---")
        #print(ref_IDM)
        #print("---ref pm original ---")
        #print(ref_PM)
        #building pm with empty idm
        self.assertFalse(self.ruleset.build_PM())
        self.assertEqual(len(self.ruleset.pm),0)
        #building idm
        self.ruleset.build_IDM()
        checked = self.ruleset.idm
        #print("ref:")
        #print(ref)
        #print("checked:")
        #print(checked)
        for i in range(a):
            for j in range(b):
                for k in range(c):
                    self.assertEqual(checked[i,j,k],ref_IDM[i,j,k])
        #building pm with existing idm
        self.assertTrue(self.ruleset.build_PM())
        checked = self.ruleset.pm
        for i in range(b):
            for j in range(c):
                self.assertEqual(checked[i,j],ref_PM[i,j])
        
    def test_connection(self):
        #Warning, value hardcoded that would need to change if values changes in class Relation
        self.assertEqual(self.ruleset.connection(0,0),Connection.ERROR)
        dummy_pm1 = [[0, 1, -1],
                    [0, 0, 0],
                    [0, 0, 0]]
        self.ruleset.pm = dummy_pm1
        self.assertEqual(self.ruleset.connection(0,0),Connection.REFERENCE)
        self.assertEqual(self.ruleset.connection(0,1),Connection.EQUAL_SAME)
        self.assertEqual(self.ruleset.connection(2,0),Connection.EQUAL_DIFF)
        self.assertEqual(self.ruleset.connection(1,2),Connection.DISCONNECTED)
        self.assertRaises(ValueError,self.ruleset.connection, 3, 0)
        self.assertRaises(ValueError,self.ruleset.connection, 1, 6)
        dummy_pm2 = [[0, -2, 4],
                    [0, 0, -66],
                    [0, 0, 0]]
        self.ruleset.pm = dummy_pm2
        self.assertEqual(self.ruleset.connection(0,1),Connection.INCLUSION_DIFF)
        self.assertEqual(self.ruleset.connection(0,2),Connection.INCLUSION_SAME)
        self.assertEqual(self.ruleset.connection(2,1),Connection.OVERLAP_DIFF)
        dummy_pm3 = [[0, 9, -27],
                    [0, 0, 18],
                    [0, 0, 0]]
        self.ruleset.pm = dummy_pm3
        self.assertEqual(self.ruleset.connection(1,0),Connection.INCLUSION_SAME)
        self.assertEqual(self.ruleset.connection(2,0),Connection.INCLUSION_DIFF)
        self.assertEqual(self.ruleset.connection(1,2),Connection.OVERLAP_SAME)
        self.assertEqual(self.ruleset.connection(2,2),Connection.REFERENCE)

    def test_val_IDC(self):
        inter1 = pd.Interval(1,6,'both')
        inter2 = pd.Interval(1,6,'neither')
        inter3 = pd.Interval(1,3,'both')
        inter4 = pd.Interval(6,8,'right')
        inter5 = pd.Interval(8,12,'neither')
        inter6 = pd.Interval(8,12,'left')
        inter7 = pd.Interval(4,9,'left')
        inter8 = pd.Interval(2,4,'neither')
        inter9 = pd.Interval(3,6,'right')
        inter10 = pd.Interval(1,6,'left')
        inter11 = pd.Interval(1,6,'right')
        inter12 = pd.Interval(1,10,'right')
        #same boudaries, different closedness
        self.assertEqual(self.ruleset._val_IDC(inter1,inter1), Relation.EQUALITY.value)
        self.assertEqual(self.ruleset._val_IDC(inter1,inter2), Relation.INCLUSION_JI.value)
        self.assertEqual(self.ruleset._val_IDC(inter2,inter1), Relation.INCLUSION_IJ.value)
        self.assertEqual(self.ruleset._val_IDC(inter1,inter10), Relation.INCLUSION_JI.value)
        self.assertEqual(self.ruleset._val_IDC(inter10,inter1), Relation.INCLUSION_IJ.value)
        self.assertEqual(self.ruleset._val_IDC(inter1,inter11), Relation.INCLUSION_JI.value)
        self.assertEqual(self.ruleset._val_IDC(inter11,inter1), Relation.INCLUSION_IJ.value)
        self.assertEqual(self.ruleset._val_IDC(inter2,inter10), Relation.INCLUSION_IJ.value)
        self.assertEqual(self.ruleset._val_IDC(inter10,inter2), Relation.INCLUSION_JI.value)
        self.assertEqual(self.ruleset._val_IDC(inter2,inter11), Relation.INCLUSION_IJ.value)
        self.assertEqual(self.ruleset._val_IDC(inter11,inter2), Relation.INCLUSION_JI.value)
        self.assertEqual(self.ruleset._val_IDC(inter10,inter11), Relation.OVERLAP.value)
        self.assertEqual(self.ruleset._val_IDC(inter11,inter10), Relation.OVERLAP.value)
        #Other
        self.assertEqual(self.ruleset._val_IDC(inter1,inter3), Relation.INCLUSION_JI.value)
        self.assertEqual(self.ruleset._val_IDC(inter3,inter1), Relation.INCLUSION_IJ.value)
        self.assertEqual(self.ruleset._val_IDC(inter1,inter8), Relation.INCLUSION_JI.value)
        self.assertEqual(self.ruleset._val_IDC(inter8,inter1), Relation.INCLUSION_IJ.value)
        self.assertEqual(self.ruleset._val_IDC(inter1,inter9), Relation.INCLUSION_JI.value)
        self.assertEqual(self.ruleset._val_IDC(inter9,inter1), Relation.INCLUSION_IJ.value)
        self.assertEqual(self.ruleset._val_IDC(inter1,inter4), Relation.DIFFERENCE.value)
        self.assertEqual(self.ruleset._val_IDC(inter1,inter5), Relation.DIFFERENCE.value)
        self.assertEqual(self.ruleset._val_IDC(inter5,inter1), Relation.DIFFERENCE.value)
        self.assertEqual(self.ruleset._val_IDC(inter4,inter5), Relation.DIFFERENCE.value)
        self.assertEqual(self.ruleset._val_IDC(inter5,inter4), Relation.DIFFERENCE.value)
        self.assertEqual(self.ruleset._val_IDC(inter5,inter6), Relation.INCLUSION_IJ.value)
        self.assertEqual(self.ruleset._val_IDC(inter6,inter5), Relation.INCLUSION_JI.value)
        self.assertEqual(self.ruleset._val_IDC(inter1,inter7), Relation.OVERLAP.value)
        self.assertEqual(self.ruleset._val_IDC(inter7,inter1), Relation.OVERLAP.value)
        self.assertEqual(self.ruleset._val_IDC(inter8,inter9), Relation.OVERLAP.value)
        self.assertEqual(self.ruleset._val_IDC(inter9,inter8), Relation.OVERLAP.value)
        self.assertEqual(self.ruleset._val_IDC(inter4,inter6), Relation.OVERLAP.value)
        self.assertEqual(self.ruleset._val_IDC(inter6,inter4), Relation.OVERLAP.value)
        self.assertEqual(self.ruleset._val_IDC(inter1,inter12), Relation.OVERLAP.value)
        self.assertEqual(self.ruleset._val_IDC(inter12,inter1), Relation.OVERLAP.value)
        self.assertEqual(self.ruleset._val_IDC(inter2,inter12), Relation.INCLUSION_IJ.value)
        self.assertEqual(self.ruleset._val_IDC(inter12,inter2), Relation.INCLUSION_JI.value)

        f1 = 3.4; f2 = 4.0; nf = np.array([3.4, 8.0])
        self.assertEqual(self.ruleset._val_IDC(f1,f1), Relation.EQUALITY.value)
        self.assertEqual(self.ruleset._val_IDC(f1,f2), Relation.DIFFERENCE.value)
        self.assertEqual(self.ruleset._val_IDC(f2,f1), Relation.DIFFERENCE.value)
        self.assertEqual(self.ruleset._val_IDC(nf[0],nf[0]), Relation.EQUALITY.value)
        self.assertEqual(self.ruleset._val_IDC(nf[0],f1), Relation.EQUALITY.value)
        self.assertEqual(self.ruleset._val_IDC(f2,nf[1]), Relation.DIFFERENCE.value)
        self.assertEqual(self.ruleset._val_IDC(nf[0],nf[1]), Relation.DIFFERENCE.value)

        nbool = np.array([False,True])
        self.assertEqual(self.ruleset._val_IDC(True,True), Relation.EQUALITY.value)
        self.assertEqual(self.ruleset._val_IDC(False,False), Relation.EQUALITY.value)
        self.assertEqual(self.ruleset._val_IDC(True,False), Relation.DIFFERENCE.value)
        self.assertEqual(self.ruleset._val_IDC(False,True), Relation.DIFFERENCE.value)
        self.assertEqual(self.ruleset._val_IDC(nbool[1],True), Relation.EQUALITY.value)
        self.assertEqual(self.ruleset._val_IDC(nbool[1],nbool[1]), Relation.EQUALITY.value)
        self.assertEqual(self.ruleset._val_IDC(nbool[0],True), Relation.DIFFERENCE.value)
        self.assertEqual(self.ruleset._val_IDC(nbool[0],nbool[1]), Relation.DIFFERENCE.value)

        nan = float('nan'); nnan = np.array([float('nan')])
        self.assertEqual(self.ruleset._val_IDC(nan,nan), Relation.EQUALITY.value)
        self.assertEqual(self.ruleset._val_IDC(nan,inter1), Relation.INCLUSION_JI.value)
        self.assertEqual(self.ruleset._val_IDC(inter3,nan), Relation.INCLUSION_IJ.value)
        self.assertEqual(self.ruleset._val_IDC(nan,f1), Relation.INCLUSION_JI.value)
        self.assertEqual(self.ruleset._val_IDC(f2,nan), Relation.INCLUSION_IJ.value)
        self.assertEqual(self.ruleset._val_IDC(nan,True), Relation.INCLUSION_JI.value)
        self.assertEqual(self.ruleset._val_IDC(False,nan), Relation.INCLUSION_IJ.value)
        self.assertEqual(self.ruleset._val_IDC(nan,nnan[0]), Relation.EQUALITY.value)
        self.assertEqual(self.ruleset._val_IDC(nnan[0],nnan[0]), Relation.EQUALITY.value)
        self.assertEqual(self.ruleset._val_IDC(nnan[0],inter1), Relation.INCLUSION_JI.value)
        self.assertEqual(self.ruleset._val_IDC(inter3,nnan[0]), Relation.INCLUSION_IJ.value)
        self.assertEqual(self.ruleset._val_IDC(nnan[0],f1), Relation.INCLUSION_JI.value)
        self.assertEqual(self.ruleset._val_IDC(f2,nnan[0]), Relation.INCLUSION_IJ.value)
        self.assertEqual(self.ruleset._val_IDC(nnan[0],nf[0]), Relation.INCLUSION_JI.value)
        self.assertEqual(self.ruleset._val_IDC(nf[1],nnan[0]), Relation.INCLUSION_IJ.value)
        self.assertEqual(self.ruleset._val_IDC(nnan[0],nbool[1]), Relation.INCLUSION_JI.value)
        self.assertEqual(self.ruleset._val_IDC(nbool[0],nnan[0]), Relation.INCLUSION_IJ.value)

        str1 = 'bla'; str2 = "bli"
        self.assertEqual(self.ruleset._val_IDC(str1,str1), Relation.EQUALITY.value)
        self.assertEqual(self.ruleset._val_IDC(str1,str2), Relation.DIFFERENCE.value)
        self.assertEqual(self.ruleset._val_IDC(str2,str1), Relation.DIFFERENCE.value)

        self.assertRaises(TypeError,self.ruleset._val_IDC,f1,inter1)
        self.assertRaises(TypeError,self.ruleset._val_IDC,nbool[0],inter1)
        self.assertRaises(TypeError,self.ruleset._val_IDC,'tre',nf[0])

        self.assertEqual(self.ruleset._val_IDC(2,2), Relation.EQUALITY.value)
        self.assertEqual(self.ruleset._val_IDC(2,3), Relation.DIFFERENCE.value)


    def test_get_val(self):
        self.assertEqual(self.ruleset.get_val(0,0),'rec1')
        self.assertEqual(self.ruleset.get_val(2,'AvgDayCons'),pd.Interval(30,120))
        self.assertRaises(ValueError,self.ruleset.get_val,3,0)
        self.assertRaises(ValueError,self.ruleset.get_val,0,'hello')
        self.assertRaises(ValueError,self.ruleset.get_val,'AvgDayCons',0)
        self.assertRaises(ValueError,self.ruleset.get_val,0,12)

    def test_has_type(self):
        b1 = True; b2 = False; b1np = np.array([True]); b2np = np.array([False])
        f1 = 7.0; f2 = 4.2; fnp = np.array([6.9, 9.6])
        inter1 = pd.Interval(5,6); inter2 = pd.Interval(7,8)

        self.assertTrue(self.ruleset.has_type(b1,bool))
        self.assertTrue(self.ruleset.has_type(b1,np.bool_))
        self.assertTrue(self.ruleset.has_type(b1np[0],bool))
        self.assertTrue(self.ruleset.has_type(b1np[0],np.bool_))
        self.assertTrue(self.ruleset.has_type(f1,float))
        self.assertTrue(self.ruleset.has_type(f1,np.float64))
        self.assertTrue(self.ruleset.has_type(fnp[0],float))
        self.assertTrue(self.ruleset.has_type(fnp[0],np.float64))
        self.assertTrue(self.ruleset.has_type(inter1,pd._libs.interval.Interval))
        self.assertFalse(self.ruleset.has_type(b1,float))
        self.assertFalse(self.ruleset.has_type(f1,np.bool_))
        self.assertFalse(self.ruleset.has_type(inter1,float))


    def test_update_val(self):
        val1 = pd.Interval(30,100) #if put in (1,0), change overlap to inclusion between r0 et r1
        val2 = True #if put in (2,3) change inclusion to overlap between r1 vs r2 and r0 vs r2
        #self.assertRaise(ValueError,self.ruleset.update_val,3,3,val1)
        self.assertRaises(ValueError,self.ruleset.update_val,3,3,val1)
        self.ruleset.update_val(0,1,val1)
        self.assertEqual(self.ruleset.get_val(0,1),val1)
        self.assertEqual(len(self.ruleset.idm),0)
        self.ruleset.update_val(0,1,float('nan'))
        self.assertTrue(pd.isna(self.ruleset.get_val(0,1)))
        #ruleset is back as original
        self.ruleset.build_IDM()
        self.ruleset.build_PM()
        ref_idm = copy.copy(self.ruleset.idm)
        ref_pm = copy.copy(self.ruleset.pm)

        self.ruleset.update_val(2,3,val2,update=False)
        self.assertEqual(self.ruleset.get_val(2,3),val2)
        for k in range(self.ruleset.m):
            for i in range(self.ruleset.n):
                for j in range(self.ruleset.n):
                    self.assertEqual(self.ruleset.idm[k,i,j],ref_idm[k,i,j])
        
        self.ruleset.update_val(2,3,val2)
        ref_idm[3,0,2] = 0
        ref_pm[0,2] = 0
        #print("-- ref idm 1 ---")
        #print(ref_idm)
        #print("--- real idm 1 ---")
        #print(self.ruleset.idm)
        self.assertEqual(self.ruleset.get_val(2,3),val2)
        for k in range(self.ruleset.m):
            for i in range(self.ruleset.n):
                for j in range(self.ruleset.n):
                    self.assertEqual(self.ruleset.idm[k,i,j],ref_idm[k,i,j])
        for i in range(self.ruleset.n):
            for j in range(self.ruleset.n):
                self.assertEqual(self.ruleset.pm[i,j],ref_pm[i,j])
        
        self.ruleset.update_val(0,1,val1)
        ref_idm[1,0,1] = 1; ref_idm[1,0,2] = 2
        ref_pm[0,1] = -4
        #print("--ref idm 2---")
        #print(ref_idm)
        #print("---real idm 2---")
        #print(self.ruleset.idm)
        self.assertEqual(self.ruleset.get_val(0,1),val1)
        for k in range(self.ruleset.m):
            for i in range(self.ruleset.n):
                for j in range(self.ruleset.n):
                    self.assertEqual(self.ruleset.idm[k,i,j],ref_idm[k,i,j])
        for i in range(self.ruleset.n):
            for j in range(self.ruleset.n):
                self.assertEqual(self.ruleset.pm[i,j],ref_pm[i,j])
        
        self.ruleset.update_val(1,3,val2)
        ref_idm[3,0,1] = 0; ref_idm[3,1,2] = 1
        ref_pm[0,1] = 0; ref_pm[1,2] = 6
        #print("--ref idm 3 ---")
        #print(ref_idm)
        #print("---real idm 3 ---")
        #print(self.ruleset.idm)
        self.assertEqual(self.ruleset.get_val(1,3),val2)
        for k in range(self.ruleset.m):
            for i in range(self.ruleset.n):
                for j in range(self.ruleset.n):
                    self.assertEqual(self.ruleset.idm[k,i,j],ref_idm[k,i,j])
        for i in range(self.ruleset.n):
            for j in range(self.ruleset.n):
                self.assertEqual(self.ruleset.pm[i,j],ref_pm[i,j])
        
        self.ruleset.update_val(0,0,'rec2')
        self.ruleset.update_val(2,0,'rec1')
        ref_idm[0,0,1] = 1; ref_idm[0,1,2] = -1
        ref_pm[1,2] = -6
        self.assertEqual(self.ruleset.get_val(0,0),'rec2')
        self.assertEqual(self.ruleset.get_val(2,0),'rec1')
        for k in range(self.ruleset.m):
            for i in range(self.ruleset.n):
                for j in range(self.ruleset.n):
                    self.assertEqual(self.ruleset.idm[k,i,j],ref_idm[k,i,j])
        for i in range(self.ruleset.n):
            for j in range(self.ruleset.n):
                self.assertEqual(self.ruleset.pm[i,j],ref_pm[i,j])

    def test_update_attr(self):
        new_attr = ['Recommendation', 'Attr1', 'Attr2', 'Attr3']
        self.ruleset.update_attr(new_attr)
        self.assertEqual(self.ruleset.attr_names,new_attr)
        self.assertEqual(self.ruleset.attr_names,new_attr)
        bad_attr = ['bad_name', 'Attr1', 'Attr2', 'Attr3']
        self.assertRaises(ValueError,self.ruleset.update_attr,bad_attr)
        self.assertEqual(self.ruleset.attr_names,new_attr)
        bad_attr = ['Rec', 'Attr1', '', 'Attr3']
        self.assertRaises(ValueError,self.ruleset.update_attr,bad_attr)   
        self.assertEqual(self.ruleset.attr_names,new_attr)     

    def test_add_attr(self):
        new_attr1 = 'New1'
        old_attr = self.ruleset.attr_names
        old_m = self.ruleset.m
        self.ruleset.add_attr(new_attr1)
        self.assertEqual(self.ruleset.attr_names, old_attr+[new_attr1])
        self.assertEqual(self.ruleset.m,old_m+1)
        self.assertTrue(pd.isna(self.ruleset.set['New1'][0]))
        self.assertTrue(pd.isna(self.ruleset.set['New1'][1]))
        self.assertTrue(pd.isna(self.ruleset.set['New1'][2]))
        self.assertEqual(len(self.ruleset.idm),0) #shows idm is not built when it was empy to start with
        ref_idm = [[[0,-1,-1],[0,0,1],[0,0,0]],[[0,3,3],[0,0,2],[0,0,0]],[[0,2,0],[0,0,3],[0,0,0]],[[0,2,1],[0,0,3],[0,0,0]],[[0,1,1],[0,0,1],[0,0,0]]]
        ref_pm = [[0,-12,0],[0,0,18],[0,0,0]]
        self.ruleset.build_IDM()
        self.ruleset.build_PM()
        #print("-- ref idm 1 ---")
        #print(ref_idm)
        #print("--- real idm 1 ---")
        #print(self.ruleset.idm)
        for k in range(self.ruleset.m):
            for i in range(self.ruleset.n):
                for j in range(self.ruleset.n):
                    self.assertEqual(self.ruleset.idm[k,i,j],ref_idm[k][i][j])
        for i in range(self.ruleset.n):
            for j in range(self.ruleset.n):
                self.assertEqual(self.ruleset.pm[i,j],ref_pm[i][j])
        
        self.ruleset.update_val(0,2,pd.Interval(25,200,'neither'))
        new_attr2 = 'New2'
        inter1 = pd.Interval(0,200); inter2 = pd.Interval(float('-inf'),float('inf')); inter3 = pd.Interval(0,100)
        new_vals = [inter1,inter2,inter3]
        ref_idm = [[[0,-1,-1],[0,0,1],[0,0,0]],[[0,3,3],[0,0,2],[0,0,0]],[[0,2,3],[0,0,3],[0,0,0]],[[0,2,1],[0,0,3],[0,0,0]],[[0,1,1],[0,0,1],[0,0,0]],[[0,2,3],[0,0,3],[0,0,0]]]
        ref_pm = [[0,-24,-27],[0,0,54],[0,0,0]]
        self.ruleset.add_attr(new_attr2,val_list=new_vals)
        #print("-- ref idm 2 ---")
        #print(ref_idm)
        #print("--- real idm 2 ---")
        #print(self.ruleset.idm)
        self.assertEqual(self.ruleset.attr_names, old_attr+[new_attr1]+[new_attr2])
        self.assertEqual(self.ruleset.m,old_m+2)
        self.assertEqual(self.ruleset.set['New2'][0],inter1)
        self.assertEqual(self.ruleset.set['New2'][1],inter2)
        self.assertEqual(self.ruleset.set['New2'][2],inter3)
        for k in range(self.ruleset.m):
            for i in range(self.ruleset.n):
                for j in range(self.ruleset.n):
                    self.assertEqual(self.ruleset.idm[k,i,j],ref_idm[k][i][j])
        for i in range(self.ruleset.n):
            for j in range(self.ruleset.n):
                self.assertEqual(self.ruleset.pm[i,j],ref_pm[i][j])

        new_attr3 = 'New3'; attr_list = [1,2,3]
        ref_idm = [[[0,-1,-1],[0,0,1],[0,0,0]],[[0,3,3],[0,0,2],[0,0,0]],[[0,2,3],[0,0,3],[0,0,0]],[[0,2,1],[0,0,3],[0,0,0]],[[0,1,1],[0,0,1],[0,0,0]],[[0,2,3],[0,0,3],[0,0,0]],[[0,0,0],[0,0,0],[0,0,0]]]
        ref_pm = [[0,0,0],[0,0,0],[0,0,0]]
        self.ruleset.add_attr(new_attr3,val_list=attr_list)
        #print("-- ref idm 3 ---")
        #print(ref_idm)
        #print("--- real idm 3 ---")
        #print(self.ruleset.idm)
        self.assertEqual(self.ruleset.attr_names, old_attr+[new_attr1]+[new_attr2]+[new_attr3])
        self.assertEqual(self.ruleset.m,old_m+3)
        self.assertEqual(len(self.ruleset.idm),old_m+3) #shows idm was updated
        self.assertEqual(self.ruleset.set['New3'][0],1)
        self.assertEqual(self.ruleset.set['New3'][1],2)
        self.assertEqual(self.ruleset.set['New3'][2],3)
        for k in range(self.ruleset.m):
            for i in range(self.ruleset.n):
                for j in range(self.ruleset.n):
                    self.assertEqual(self.ruleset.idm[k,i,j],ref_idm[k][i][j])
        for i in range(self.ruleset.n):
            for j in range(self.ruleset.n):
                self.assertEqual(self.ruleset.pm[i,j],ref_pm[i][j])

        new_attr3 = 'New3'
        self.assertRaises(ValueError,self.ruleset.add_attr,new_attr3)
        self.assertEqual(self.ruleset.attr_names,old_attr+[new_attr1]+[new_attr2]+[new_attr3])

        new_attr4 = ''
        self.assertRaises(ValueError,self.ruleset.add_attr,new_attr3)
        self.assertEqual(self.ruleset.attr_names,old_attr+[new_attr1]+[new_attr2]+[new_attr3])

    def test_add_rule(self):
        self.ruleset.build_IDM()
        self.ruleset.build_PM()
        old_n = self.ruleset.n
        rec_name1 = 'NewRec'
        self.ruleset.add_rule(rec_name1)
        self.assertEqual(self.ruleset.n,old_n+1)
        self.assertEqual(len(self.ruleset.set),old_n+1) #shows ruleset has one more rule
        self.assertEqual(self.ruleset.get_val(old_n,0),rec_name1)
        for i in range(1,self.ruleset.m):
            self.assertTrue(pd.isna(self.ruleset.set.iloc[old_n,i]))
        ref_idm = [[[0,-1,-1,-1],[0,0,1,-1],[0,0,0,-1],[0,0,0,0]],[[0,3,3,1],[0,0,2,2],[0,0,0,2],[0,0,0,0]],[[0,2,0,2],[0,0,3,1],[0,0,0,2],[0,0,0,0]],[[0,2,1,2],[0,0,3,1],[0,0,0,2],[0,0,0,0]]]
        ref_pm = [[0,-12,0,-4],[0,0,18,-2],[0,0,0,-8],[0,0,0,0]]
        for k in range(self.ruleset.m):
            for i in range(self.ruleset.n):
                for j in range(self.ruleset.n):
                    self.assertEqual(self.ruleset.idm[k,i,j],ref_idm[k][i][j])
        for i in range(self.ruleset.n):
            for j in range(self.ruleset.n):
                self.assertEqual(self.ruleset.pm[i,j],ref_pm[i][j])
        
        rec_name2 = 'rec4'; new_vals = [pd.Interval(30,100),float('nan'),float('nan')]
        self.ruleset.add_rule(rec_name2, new_vals)
        ref_idm = [[[0,-1,-1,-1,-1],[0,0,1,-1,-1],[0,0,0,-1,-1],[0,0,0,0,-1],[0,0,0,0,0]],[[0,3,3,1,3],[0,0,2,2,1],[0,0,0,2,3],[0,0,0,0,3],[0,0,0,0,0]],[[0,2,0,2,2],[0,0,3,1,1],[0,0,0,2,2],[0,0,0,0,1],[0,0,0,0,0]],[[0,2,1,2,2],[0,0,3,1,1],[0,0,0,2,2],[0,0,0,0,1],[0,0,0,0,0]]]
        ref_pm = [[0,-12,0,-4,-12],[0,0,18,-2,-1],[0,0,0,-8,-12],[0,0,0,0,-3],[0,0,0,0,0]]
        self.assertEqual(self.ruleset.n,old_n+2)
        self.assertEqual(self.ruleset.set['Rec'][self.ruleset.n-1],rec_name2)
        self.assertEqual(self.ruleset.set['AvgDayCons'][self.ruleset.n-1],pd.Interval(30,100))
        self.assertTrue(pd.isna(self.ruleset.set['AvgNightCons'][self.ruleset.n-1]))
        self.assertTrue(pd.isna(self.ruleset.set['InCommunity'][self.ruleset.n-1]))
        for k in range(self.ruleset.m):
            for i in range(self.ruleset.n):
                for j in range(self.ruleset.n):
                    self.assertEqual(self.ruleset.idm[k,i,j],ref_idm[k][i][j])
        for i in range(self.ruleset.n):
            for j in range(self.ruleset.n):
                self.assertEqual(self.ruleset.pm[i,j],ref_pm[i][j])

        rec_name3 = 'rec1'; new_vals = [float('nan'),pd.Interval(100,175),False]
        self.ruleset.add_rule(rec_name3, new_vals)
        ref_idm = [[[0,-1,-1,-1,-1,1],[0,0,1,-1,-1,-1],[0,0,0,-1,-1,-1],[0,0,0,0,-1,-1],[0,0,0,0,0,-1],[0,0,0,0,0,0]],[[0,3,3,1,3,1],[0,0,2,2,1,2],[0,0,0,2,3,2],[0,0,0,0,3,1],[0,0,0,0,0,2],[0,0,0,0,0,0]],[[0,2,0,2,2,6],[0,0,3,1,1,3],[0,0,0,2,2,6],[0,0,0,0,1,3],[0,0,0,0,0,3],[0,0,0,0,0,0]],[[0,2,1,2,2,1],[0,0,3,1,1,3],[0,0,0,2,2,1],[0,0,0,0,1,3],[0,0,0,0,0,3],[0,0,0,0,0,0]]]
        ref_pm = [[0,-12,0,-4,-12,6],[0,0,18,-2,-1,-18],[0,0,0,-8,-12,-12],[0,0,0,0,-3,-9],[0,0,0,0,0,-18],[0,0,0,0,0,0]]
        self.assertEqual(self.ruleset.n,old_n+3)
        self.assertEqual(self.ruleset.set['Rec'][self.ruleset.n-1],rec_name3)
        self.assertTrue(pd.isna(self.ruleset.set['AvgDayCons'][self.ruleset.n-1]))        
        self.assertEqual(self.ruleset.set['AvgNightCons'][self.ruleset.n-1],pd.Interval(100,175))
        self.assertEqual(self.ruleset.set['InCommunity'][self.ruleset.n-1],False)
        for k in range(self.ruleset.m):
            for i in range(self.ruleset.n):
                for j in range(self.ruleset.n):
                    self.assertEqual(self.ruleset.idm[k,i,j],ref_idm[k][i][j])
        for i in range(self.ruleset.n):
            for j in range(self.ruleset.n):
                self.assertEqual(self.ruleset.pm[i,j],ref_pm[i][j])
        
        self.assertRaises(ValueError,self.ruleset.add_rule,'hello',[3.0])

    def test_delete_attr(self):
        old_m = self.ruleset.m
        self.ruleset.build_IDM()
        self.ruleset.build_PM()

        del_attr1 = 'AvgDayCons'
        self.ruleset.delete_attr(del_attr1)
        #print("ruleset after del AvgDayCons")
        #print(self.ruleset)
        ref_idm = [[[0,-1,-1],[0,0,1],[0,0,0]],[[0,2,0],[0,0,3],[0,0,0]],[[0,2,1],[0,0,3],[0,0,0]]]
        ref_pm = [[0,-4,0],[0,0,9],[0,0,0]]
        self.assertTrue(del_attr1 not in self.ruleset.set.columns.tolist())
        self.assertTrue(del_attr1 not in self.ruleset.attr_names)
        self.assertEqual(self.ruleset.m,old_m-1)
        for k in range(self.ruleset.m):
            for i in range(self.ruleset.n):
                for j in range(self.ruleset.n):
                    self.assertEqual(self.ruleset.idm[k,i,j],ref_idm[k][i][j])
        for i in range(self.ruleset.n):
            for j in range(self.ruleset.n):
                self.assertEqual(self.ruleset.pm[i,j],ref_pm[i][j])

        del_attr2 = 'InCommunity'
        self.ruleset.delete_attr(del_attr2)
        #print("ruleset after del InCommunity")
        #print(self.ruleset)
        ref_idm = [[[0,-1,-1],[0,0,1],[0,0,0]],[[0,2,0],[0,0,3],[0,0,0]]]
        ref_pm = [[0,-2,0],[0,0,3],[0,0,0]]
        self.assertTrue(del_attr2 not in self.ruleset.set.columns.tolist())
        self.assertTrue(del_attr2 not in self.ruleset.attr_names)
        self.assertEqual(self.ruleset.m,old_m-2)
        for k in range(self.ruleset.m):
            for i in range(self.ruleset.n):
                for j in range(self.ruleset.n):
                    self.assertEqual(self.ruleset.idm[k,i,j],ref_idm[k][i][j])
        for i in range(self.ruleset.n):
            for j in range(self.ruleset.n):
                self.assertEqual(self.ruleset.pm[i,j],ref_pm[i][j])
        
        del_attr3 = 'AvgNightCons'
        self.ruleset.delete_attr(1)
        #print("ruleset after del AvgNightCons")
        #print(self.ruleset)
        ref_idm = [[[0,-1,-1],[0,0,1],[0,0,0]]]
        ref_pm = [[0,-1,-1],[0,0,1],[0,0,0]]
        self.assertTrue(del_attr3 not in self.ruleset.set.columns.tolist())
        self.assertTrue(del_attr3 not in self.ruleset.attr_names)
        self.assertEqual(self.ruleset.m,old_m-3)
        for k in range(self.ruleset.m):
            for i in range(self.ruleset.n):
                for j in range(self.ruleset.n):
                    self.assertEqual(self.ruleset.idm[k,i,j],ref_idm[k][i][j])
        for i in range(self.ruleset.n):
            for j in range(self.ruleset.n):
                self.assertEqual(self.ruleset.pm[i,j],ref_pm[i][j])

        self.assertRaises(ValueError,self.ruleset.delete_attr,2)
        self.assertRaises(ValueError,self.ruleset.delete_attr,'Hello')
        self.assertRaises(ValueError,self.ruleset.delete_attr,'Rec')

    def test_delete_rule_1(self):
        old_n = self.ruleset.n
        old_attr = self.ruleset.attr_names
        self.ruleset.build_IDM()
        self.ruleset.build_PM()

        self.ruleset.delete_rule(1) #rule in the middle
        ref_idm = [[[0,-1],[0,0]],[[0,3],[0,0]],[[0,0],[0,0]],[[0,1],[0,0]]]
        ref_pm = [[0,0],[0,0]]
        self.assertEqual(len(self.ruleset.set),old_n-1)
        self.assertEqual(self.ruleset.n,old_n-1)
        self.assertEqual(self.ruleset.set.columns.tolist(),old_attr)
        self.assertEqual(self.ruleset.set.index.tolist(),[0,1])
        #print("-- ref idm 1 ---")
        #print(ref_idm)
        #print("--- real idm 1 ---")
        #print(self.ruleset.idm)
        for k in range(self.ruleset.m):
            for i in range(self.ruleset.n):
                for j in range(self.ruleset.n):
                    self.assertEqual(self.ruleset.idm[k,i,j],ref_idm[k][i][j])
        for i in range(self.ruleset.n):
            for j in range(self.ruleset.n):
                self.assertEqual(self.ruleset.pm[i,j],ref_pm[i][j])

        self.ruleset.delete_rule(1) #rule at the end
        ref_idm = [[[0],[0]],[[0],[0]],[[0],[0]],[[0],[0]]]
        ref_pm = [[0]]
        self.assertEqual(len(self.ruleset.set),old_n-2)
        self.assertEqual(self.ruleset.n,old_n-2)
        self.assertEqual(self.ruleset.set.columns.tolist(),old_attr)
        self.assertEqual(self.ruleset.set.index.tolist(),[0])
        self.assertEqual(len(self.ruleset.idm),0)
        self.assertEqual(len(self.ruleset.idm),0)

        self.ruleset.delete_rule(0) #last remaning rule
        self.assertEqual(len(self.ruleset.set),0)
        self.assertEqual(self.ruleset.n,0)
        self.assertEqual(self.ruleset.set.columns.tolist(),old_attr)
        self.assertEqual(self.ruleset.set.index.tolist(),[])
        self.assertFalse(self.ruleset.idm.any())
        self.assertFalse(self.ruleset.pm.any())
        self.assertEqual(len(self.ruleset.idm),0)
        self.assertEqual(len(self.ruleset.idm),0)
        
    def test_delete_rule_2(self):
        old_n = self.ruleset.n
        old_attr = self.ruleset.attr_names
        self.ruleset.build_IDM()
        self.ruleset.build_PM()

        self.ruleset.delete_rule(0) #first rule
        ref_idm = [[[0,1],[0,0]],[[0,2],[0,0]],[[0,3],[0,0]],[[0,3],[0,0]]]
        ref_pm = [[0,18],[0,0]]
        self.assertEqual(len(self.ruleset.set),old_n-1)
        self.assertEqual(self.ruleset.n,old_n-1)
        self.assertEqual(self.ruleset.set.columns.tolist(),old_attr)
        self.assertEqual(self.ruleset.set.index.tolist(),[0,1])
        #print("-- ref idm 1 ---")
        #print(ref_idm)
        #print("--- real idm 1 ---")
        #print(self.ruleset.idm)
        for k in range(self.ruleset.m):
            for i in range(self.ruleset.n):
                for j in range(self.ruleset.n):
                    self.assertEqual(self.ruleset.idm[k,i,j],ref_idm[k][i][j])
        for i in range(self.ruleset.n):
            for j in range(self.ruleset.n):
                self.assertEqual(self.ruleset.pm[i,j],ref_pm[i][j])

    def test_same_type(self):
        b1 = True; b2 = False; b1np = np.array([True]); b2np = np.array([False])
        f1 = 7.0; f2 = 4.2; fnp = np.array([6.9, 9.6])
        inter1 = pd.Interval(5,6); inter2 = pd.Interval(7,8)

        self.assertTrue(self.ruleset.same_type(b1,b2))
        self.assertTrue(self.ruleset.same_type(b1,b1np[0]))
        self.assertTrue(self.ruleset.same_type(b1np[0],b2np[0]))
        self.assertTrue(self.ruleset.same_type(f1,f2))
        self.assertTrue(self.ruleset.same_type(f1,fnp[0]))
        self.assertTrue(self.ruleset.same_type(fnp[1],fnp[0]))
        self.assertTrue(self.ruleset.same_type(inter1,inter2))
        self.assertFalse(self.ruleset.same_type(b1,fnp[0]))
        self.assertFalse(self.ruleset.same_type(f1,b2))
        self.assertFalse(self.ruleset.same_type(inter2,fnp[0]))

class TestExtremeCases(unittest.TestCase):
    
    def test_init_empty(self):
        rset = rs.RuleSet([])
        self.assertEqual(len(rset.set),0)
        self.assertEqual(rset.m,0)
        self.assertEqual(rset.n,0)
        self.assertEqual(len(rset.idm),0)
        self.assertEqual(len(rset.pm),0)
        self.assertEqual(rset.attr_names,[])

    def test_idm_pm(self):
        # computation of idm and pm when there is only one rule in set
        r1 = {'AvgNightCons':pd.Interval(150.0,200.0, 'neither'),'InCommunity':False, 'Rec':'rec1'}
        r2 = {'AvgDayCons':pd.Interval(30.0,100.0), 'Rec':'rec2'}
        r3 = {'AvgDayCons':pd.Interval(30.0,120.0),'AvgNightCons':pd.Interval(50.0,150.0),'InCommunity':False, 'Rec':'rec2'}
        rules = [r1]
        ruleset = rs.RuleSet(rules)
        ruleset.build_IDM()
        ruleset.build_PM()
        self.assertEqual(len(ruleset.idm),0)
        self.assertEqual(len(ruleset.idm),0)

    def test_add_rule(self):
        #add rule to empty ruleset
        rset = rs.RuleSet([])
        rec_name1 = 'NewRec'
        rset.add_rule(rec_name1)
        self.assertEqual(rset.n,1)
        self.assertEqual(rset.m,1)
        self.assertEqual(rset.attr_names,['Recommendation'])
        self.assertEqual(len(rset.set),1)
        self.assertEqual(rset.set['Recommendation'][0],rec_name1)

        rset = rs.RuleSet([])
        rec_name2 = 'NewRec'; values = [float('nan'),pd.Interval(100,175),False]
        rset.add_rule(rec_name2, values)
        self.assertEqual(rset.n,1)
        self.assertEqual(rset.m,4)
        self.assertEqual(rset.attr_names,['Recommendation', 'Attr 1', 'Attr 2', 'Attr 3'])
        self.assertEqual(len(rset.set),1)
        self.assertEqual(rset.set['Recommendation'][0],rec_name2)
        self.assertTrue(pd.isna(rset.set['Attr 1'][0]))
        self.assertEqual(rset.set['Attr 2'][0],pd.Interval(100,175))
        self.assertEqual(rset.set['Attr 3'][0],False)


        


if __name__ == '__main__':
    unittest.main()