#!/usr/local/bin/python
# -*- coding: utf-8 -*-
'''
@author: melon
'''
import re
import json

def ParseParser(parser):
    #test = "#{0}:{1}-{2};"
     #TODO: DE LOS GRANDES: Este parser extrae los componentes por orden y no por el número que tienen designado.
     
    pattern = r'[{]\d+[}]'
    regex = re.compile(pattern,re.IGNORECASE)
    #print regex
    parsed = []
    for idx,match in enumerate(regex.finditer(parser)):
        parsed.append({'start':match.start(),'end':match.end(),'position':match.group(0).replace('{','').replace('}','')})
        #print "%s: %s-%s: %s" % (str(idx),match.start(),match.end(),match.group(0))
    total = len(parsed)
    for idx,group in enumerate(parsed):
        if(idx == (total-1)):#special case for the last one or in case there is only 1
            if(idx == 0):
                start_idex = 0
            else:
                start_idex = parsed[idx-1]['end']
            prec = parser[start_idex:group['start']]
            post = parser[group['end']:len(parser)]
        elif(idx == 0):#special case for first one
            prec = parser[0:group['start']]
            post = parser[group['end']:parsed[idx+1]['start']]
        else:#generic case
            prec = parser[parsed[idx-1]['end']:group['start']]
            post = parser[group['end']:parsed[idx+1]['start']]
            
        parsed[idx]['prec'] = prec
        parsed[idx]['post'] = post
            
    #print (json.dumps(parsed, indent=4, sort_keys=True))
    
    return parsed


def ParseFunction(function):
    #test = "#{0}:{1}-{2};"
     #TODO: DE LOS GRANDES: Este parser extrae los componentes por orden y no por el número que tienen designado.
     
    pattern = r'[{]\d[}]'
    regex = re.compile(pattern,re.IGNORECASE)
    #print regex
    parsed = {}
    for idx,match in enumerate(regex.finditer(function)):
        parsed[function[match.start()+1]] = {'start':match.start(),'end':match.end()}
        #print "%s: %s-%s: %s" % (str(idx),match.start(),match.end(),match.group(0))


    #print json.dumps(parsed, indent=4, sort_keys=True)
    return parsed
