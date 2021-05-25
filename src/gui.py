import PySimpleGUI as sg
import pandas as pd
import copy
import collections as col


import utils
from rule_set import * 
from connection import *

#Global variables
nbr_rows = 9
nbr_cols = 6
width = 14
ruleset = RuleSet([])
window = None
colors = {Connection.REFERENCE: 'orchid4', Connection.DISCONNECTED: 'white', Connection.EQUAL_DIFF:'DeepSkyBlue4' , Connection.INCLUSION_DIFF:'DeepSkyBlue3' , Connection.OVERLAP_DIFF:'SkyBlue1' , Connection.EQUAL_SAME:'SpringGreen4' , Connection.INCLUSION_SAME:'SpringGreen3' , Connection.OVERLAP_SAME:'pale green' }

def run_gui():
    global nbr_cols
    global nbr_rows
    global width
    global ruleset
    global window
    #Layout and window creation
    #WARNING: Any change made here has to be reproduced in resized_window()
    intro = [sg.Text('Energy rules',key = 'txt1')]
    header_row = [[sg.Text('', size=(4,1))] + [sg.Input(size=(width,1), pad=(0,0), key=(-1,attr)) for attr in range(nbr_cols)]]
    input_rows = [[sg.Text(str(row), size=(4,1))] + [sg.Input(size=(width,1), pad=(0,0), key=(row,attr)) for attr in range(nbr_cols)] + [sg.Text('', size=(2*width,1), key=('connection',row))] for row in range(nbr_rows)]
    scrollable_set = [sg.Column(header_row + input_rows, size=(width*(nbr_cols+1)*8,nbr_rows*25), scrollable=True)]
    actions1 = [sg.Text('Index of rule to check connections with:'), sg.Input(size=(4,1),key='to_check'),sg.Button('Check')]
    actions2 = [sg.Button('Update'), sg.Button('Delete rule:'), sg.Input(size=(4,1),key='del_rule'), sg.Button('Delete attribute:'), sg.Input(size=(width,1),key='del_attr')]
    actions3 = [sg.Open(), sg.Button('Increase Table size'), sg.Button('Remove changes'), sg.Button('Delete ruleset'), sg.Button('Update & Save'), ]

    layout = [intro,
            scrollable_set,
            actions1,
            actions2,
            actions3
        ]

    window = sg.Window('Rules manager', return_keyboard_events=True, finalize=True).Layout(layout)

    #Boolean to remember tasks status
    load_waiting = False
    while True:   
        event, values = window.read()
        #Execution of events that needed a modification of the window
        if load_waiting: #display loaded ruleset in table
            print("in load waiting")
            display_set(window)
            load_waiting = False
        if event in (sg.WIN_CLOSED, 'Cancel'):
            break
        elif event == 'Open':
            filename = sg.popup_get_file('filename to open', no_window=True, file_types=(("CSV Files", "*.csv"),))
            if filename is not None and type(filename) in (str,bytes):
                try:
                    rules = utils.parse_csv(filename)
                    ruleset = RuleSet(rules)
                except ValueError:
                    sg.popup_ok("File selected doesn't contain values in the right format",non_blocking=True)
                    pass
                except FileNotFoundError:
                    pass
                #print(ruleset)
                if ruleset.n >= nbr_rows or ruleset.m >= nbr_cols:
                    #create a window of appropriate size
                    #nbr_rows = ruleset.n + 3; nbr_cols = ruleset.m + 3
                    resize_window(ruleset.n + 3, ruleset.m + 3)
                    load_waiting = True  #remember that the data has yet to be loaded, which has to wait for the next pass through the while loop
                    sg.popup_ok("Resizing of window ongoing. Press any key as soon as new window appears in order to display the ruleset.", non_blocking=True, keep_on_top=True)
                else:
                    erase(window,headers=True,values=True,connections=True)
                    display_set(window)
        elif event == 'Check':
            if ruleset.n < 2:
                sg.popup_ok("You must have a ruleset with at least two rules to compare them.")
            else:
                if len(ruleset.idm) == 0:
                    ruleset.build_IDM()
                    ruleset.build_PM()
                ref = values['to_check']
                if ref == '':
                    sg.popup_ok("You need to input the index of the reference rule.")
                else:
                    try:
                        ref = int(ref)
                        if ref < 0 or ref >= ruleset.n:
                            sg.popup_ok("Input value must be a valid rule index (integer in [0," + str(ruleset.n-1) + "]")
                        else:
                            for i in range(ruleset.n):
                                con = ruleset.connection(ref,i)
                                con_elem = window[('connection',i)]
                                con_elem.update(con.value)
                                for j in range(ruleset.m):
                                    window[(i,j)].Widget.configure(background=colors[con])
                    except ValueError as ve:
                        sg.popup_ok(str(ve) + "\nInput value must be an integer")
        elif event == 'Update':
            success = update(values)
            if success:
                erase(window,connections=True)
        elif event == 'Update & Save':
            success = update(values)
            if success:
                erase(window,connections=True)
                file_name = sg.popup_get_file("Save the ruleset in a new or existing file.",save_as=True,file_types=(("CSV Files", "*.csv"),))
                ruleset.to_csv(file_name)
        elif event == 'Delete rule:':
            del_rule = values['del_rule']
            if del_rule == '':
                sg.popup_ok("You need to input the index of the rule to delete.")
            else:
                try:
                    del_rule = int(del_rule)
                    if del_rule < 0 or del_rule >= ruleset.n:
                        sg.popup_ok("Input value must be a valid rule index (integer in [0," + str(ruleset.n-1) + "]")
                    else:
                        ruleset.delete_rule(del_rule)
                        erase(window,True,True,True)
                        display_set(window)
                except ValueError as ve:
                    sg.popup_ok(str(ve) + "\nInput value must be an integer")
        elif event == 'Delete attribute:':
            del_attr = values['del_attr']
            if del_attr == '':
                sg.popup_ok("You need to input the index of the attribute to delete.")
            else:
                del_ok = True
                try:
                    del_attr = int(del_attr)
                    if del_attr < 0 or del_attr >= ruleset.m:
                        del_ok = False
                        sg.popup_ok("Input value must be a string or an index corresponding to an existing attributes.")
                except:
                    if del_attr not in ruleset.attr_names:
                        del_ok = False
                        sg.popup_ok("Input value must be a string or an index corresponding to an existing attributes.")
                if del_ok:
                    try:
                        ruleset.delete_attr(del_attr)
                        erase(window,True,True,True)
                        display_set(window)
                    except ValueError as ve:
                        sg.popup_ok(ve)
        elif event == 'Increase Table size':
            resize_window(nbr_rows + 3, nbr_cols + 3)
            load_waiting = True  #remember that the ruleset needs to be displayed again, which has to wait for the next pass through the while loop
            sg.popup_ok("Resizing of window ongoing. Press any key as soon as new window appears in order to display the ruleset.", non_blocking=True, keep_on_top=True)
        elif event == 'Remove changes':
            erase(window,headers=True,values=True,connections=True)
            display_set(window)
        elif event == 'Delete ruleset':
            answer = sg.popup_ok_cancel("No unsaved changes will be saved. Proceed to clear?")
            print(answer)
            if answer == 'OK':
                ruleset = RuleSet([])
                erase(window,headers=True,values=True,connections=True)

    window.close()

def erase(window,headers=False,values=False,connections=False):
    if headers:
        [window[(-1,j)].update('') for j in range(nbr_cols)] #empty headers
    if values:
        [window[(i,j)].update('') for j in range(nbr_cols) for i in range(nbr_rows)] #empty values
    if connections:
        [window[('connection',i)].update('') for i in range(nbr_rows)] #empty connections
        for i in range(nbr_rows):
            for j in range(nbr_cols):
                window[(i,j)].Widget.configure(background='white')         

def resize_window(rows,cols):
    global nbr_rows
    global nbr_cols
    global width
    global window
    nbr_rows = rows; nbr_cols = cols
    intro = [sg.Text('Energy rules',key = 'txt1')]
    header_row = [[sg.Text('', size=(4,1))] + [sg.Input(size=(width,1), pad=(0,0), key=(-1,attr)) for attr in range(nbr_cols)]]
    input_rows = [[sg.Text(str(row), size=(4,1))] + [sg.Input(size=(width,1), pad=(0,0), key=(row,attr)) for attr in range(nbr_cols)] + [sg.Text('', size=(2*width,1), key=('connection',row))] for row in range(nbr_rows)]
    n = min(25,nbr_rows); m = min(15,nbr_cols)
    scrollable_set = [sg.Column(header_row + input_rows, size=(width*m*8,n*25), scrollable=True)]
    actions1 = [sg.Text('Index of rule to check connections with:'), sg.Input(size=(4,1),key='to_check'),sg.Button('Check')]
    actions2 = [sg.Button('Update'), sg.Button('Delete rule:'), sg.Input(size=(4,1),key='del_rule'), sg.Button('Delete attribute:'), sg.Input(size=(width,1),key='del_attr')]
    actions3 = [sg.Open(), sg.Button('Increase Table size'), sg.Button('Remove changes'), sg.Button('Delete ruleset'), sg.Button('Update & Save'), ]
    layout = [intro, scrollable_set, actions1, actions2, actions3]
    new_window = sg.Window('Window Title', return_keyboard_events=True).Layout(layout)
    window.close()
    window = new_window
    
def display_set(window):
    global ruleset
    for k in range(ruleset.m):
        elem = window[(-1,k)]
        val = ruleset.attr_names[k]
        elem.update(val)
    for i in range(ruleset.n):
        for j in range(ruleset.m):
            try:
                elem = window[(i,j)]
                val = ruleset.get_val(i,j)
                if elem is not None:# and val is not float('nan'):
                    if type(val) is bool:
                        #Necessary to avoid a change from boolean to int
                        if val: elem.update('True')
                        else: elem.update('False')
                    else:
                        elem.update(val)
            except:
                pass

def update(values):
    global ruleset
    global nbr_rows
    global nbr_cols
    print("start update")
    problem = False
    name_change = False
    rule_to_add = False
    attr_to_add = False
    old_set = copy.deepcopy(ruleset)
    warning = "\nNo changes were saved. Try again after fixing values."

    #filling in ruleset that was empty, no previous loop has been entered since self.m == 0 and self.n == 0
    if ruleset.n == 0 and (values[0,0] != '' or values[-1,0] != ''):
        if values[(-1,0)] != 'Rec' and values[(-1,0)] != 'Recommendation':
            problem = True
            sg.popup_ok("Your ruleset needs attributes names with the first one being 'Rec' or 'Recommendation.")
        if values[0,0] == '':
            problem = True
            sg.popup_ok("Your ruleset needs at least one rule to be created")
        attributes = []; j=0
        while values[(-1,j)] != '' and j < nbr_cols:
            attributes += [values[(-1,j)]]
            j += 1
        rules_list = []
        i = 0
        while values[(i,0)] != '' and i < nbr_rows:
            vals = [values[(i,0)]]
            for j in range(1,len(attributes)):
                input_str = values[(i,j)]
                try:
                    input_val = utils.parse_val(input_str)
                    vals += [input_val]
                except ValueError as ve:
                    problem = True
                    sg.popup_ok(str(ve) + " Position: ("+str(i)+","+str(j)+")"+warning)
                    break
            rule_dict = col.OrderedDict({k:v for k,v in zip(attributes,vals)})
            print("rule dict: "+str(rule_dict))
            rules_list += [rule_dict]
            i+=1
        ruleset = RuleSet(rules_list)
        print("ruleset has been created with rule list:" + str(rules_list))
    
    #Check for change in attribute names
    for j in range(old_set.m):
        if values[(-1,j)] != old_set.attr_names[j]:
            old_set.attr_names[j] = values[(-1,j)]
            name_change = True
    if name_change:
        try:
            ruleset.update_attr(old_set.attr_names)
        except ValueError as ve:
            problem = True
            sg.popup_ok(str(ve)+warning)

    #Check for new rules (without verifying compatibility of attribute value types)
    for i in range(ruleset.n,nbr_rows):
        if values[(i,0)] != '':
            if i != ruleset.n:
                problem = True
                sg.popup_ok("New rule must be added on first available row."+warning)
            else:
                rec_str = values[(i,0)]
                val_list = []
                for j in range(1,ruleset.m):
                    input_str = values[(i,j)]
                    try:
                        input_val = utils.parse_val(input_str)
                        val_list += [input_val]
                        rule_to_add = True
                    except ValueError:
                        problem = True
                        sg.popup_ok("Value in new rule doesn't have an appropriate format. Value: "+str(input_str)+ " Position: ("+str(i)+","+str(j)+")"+warning)
                if rule_to_add:
                    try:
                        print("rule to add: " + str(rec_str)+" "+str(val_list))
                        ruleset.add_rule(rec_str,val_list)
                    except ValueError as ve:
                        problem = True
                        sg.popup_ok(str(ve)+warning)
                    except TypeError as te:
                        problem = True
                        sg.popup_ok(str(te)+warning)

    #Check for new attributes (without verifying compatibility of attribute value types)
    for j in range(ruleset.m,nbr_cols):
        print(ruleset.m)
        if values[(-1,j)] != '':
            if ruleset.n > 0 and j != ruleset.m:
                problem = True
                sg.popup_ok("New attribute must be added on first available column."+warning)
            else:
                attributes = values[(-1,j)]
                val_list = []
                for i in range(0,ruleset.n):
                        input_str = values[(i,j)]
                        try:
                            input_val = utils.parse_val(input_str)
                            val_list += [input_val]
                            attr_to_add = True
                        except ValueError:
                            problem = True
                            sg.popup_ok("Value in new attribute doesn't have an appropriate format. Value: "+str(input_str)+ " Position: ("+str(i)+","+str(j)+")"+warning)
                if attr_to_add:
                    try:
                        ruleset.add_attr(attributes,val_list)
                    except ValueError as ve:
                        problem = True
                        sg.popup_ok(str(ve)+warning)
                    except TypeError as te:
                        problem = True
                        sg.popup_ok(str(te)+warning)

    print("n: "+str(ruleset.n))
    
    #Check for changes in values and verifies compatibility between types (includes values of new rules and attributes to include them in the type compatibility check)
    if not problem:
        #Check in recommendations (type is string so no verification to perform)
        for i in range(old_set.n):
            input_str = values[(i,0)]
            if input_str != ruleset.get_val(i,0): #recommendation has been changed
                ruleset.update_val(i,0,input_str)
        #Check for other values
        for j in range(1,ruleset.m):
            col_type = None
            for i in range(ruleset.n):
                input_str = values[(i,j)]
                try:
                    input_val = utils.parse_val(input_str)
                    old_val = ruleset.get_val(i,j)
                    #Check for type mismatch within column
                    if col_type is None and not pd.isna(input_val):
                        col_type = type(input_val)
                    if (not pd.isna(input_val)) and (col_type is not None) and (not ruleset.has_type(input_val,col_type)):
                            problem = True
                            sg.popup_ok("Wrong value type for attribute " + ruleset.attr_names[j] + " in rule " + str(i) + " or a preceding one."+warning)
                            print("inputval: "+str(type(input_val))+str(input_val)+" old_val: "+str(type(old_val))+str(old_val)+ " col_type: "+str(col_type))
                            print("ruleset.same_type(input_val,col_type): " + str(ruleset.same_type(input_val,col_type)))
                            break #Avoid to show error for every following rule
                    else:
                        #Check for value change. Necessary to check for types to notice difference between int 1 or 0 and booleans
                        if input_val != old_val or not ruleset.same_type(input_val,old_val):
                            #print("input_val type: " +str(type(input_val)) + "old_val type: " +str(type(old_val)))
                            try:
                                print("input_val type: " +str(type(input_val)) + str(input_val)+ "old_val type: " +str(type(old_val))+str(old_val) + " col_type "+str(col_type))
                                ruleset.update_val(i,j,input_val)
                            except TypeError:
                                problem = True
                                sg.popup_ok("Not all values of attribute " + ruleset.attr_names[j] + " have the same type."+warning)
                except ValueError as ve:
                    problem = True
                    sg.popup_ok(str(ve) + " Position: ("+str(i)+","+str(j)+")"+warning)

    #check for the presence of inputs outside of the range of considered rules and attributes
    if not problem:
        for i in range(ruleset.n,nbr_rows):
            for j in range(1,nbr_cols):
                if values[(i,j)] != '':
                    sg.popup_ok("The input at position ("+str(i)+","+str(j)+") falls outside of the considered rules and attributes and was not saved in the ruleset.")
        for j in range(ruleset.m,nbr_cols):
            for i in range(ruleset.n):
                if values[(i,j)] != '':
                    sg.popup_ok("The input at position ("+str(i)+","+str(j)+") falls outside of the considered rules and attributes and was not saved in the ruleset.")

    if problem:
        # update could not be completed => restore original state of ruleset in memory
        ruleset = copy.deepcopy(old_set)
        print("problem")
        print(ruleset)
        print("n: "+str(ruleset.n))
        #print("---idm---")
        #print(ruleset.idm)
        #print("---pm---")
        #print(ruleset.pm)
        return False
    else:
        print("success")
        print(ruleset)
        #print("---idm---")
        #print(ruleset.idm)
        #print("---pm---")
        #print(ruleset.pm)
        return True
    
run_gui()