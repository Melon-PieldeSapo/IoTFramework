test = "#{0}:{1};"
 
import re
regex = re.compile(test,re.IGNORECASE)
 
pattern = r'[{]\d[}]'
regex = re.compile(pattern,re.IGNORECASE)
print regex
parsed = []
for idx,match in enumerate(regex.finditer(test)):
    parsed.append({'start':match.start(),'end':match.end()})
    print "%s: %s-%s: %s" % (str(idx),match.start(),match.end(),match.group(0))

print parsed

total = len(parsed)
for idx,group in enumerate(parsed):
    if(idx == 0):#special case for first one
        prec = test[0:group['start']]
        post = test[group['end']:parsed[idx+1]['start']]
    elif(idx == (total-1)):#special case for the last one
        prec = test[parsed[idx-1]['end']:group['start']]
        post = test[group['end']:len(test)]
    else:#generic case
        prec = test[parsed[idx-1]['end']:group['start']]
        post = test[group['end']:parsed[idx+1]['start']]
        
    parsed[idx]['prec'] = prec
    parsed[idx]['post'] = post
print parsed
#De esto sacar un array para valor donde se guarda el preceding string y el postceding string. (en caso de no haber al principio o al final se guarda un -1

#Para procesar el payload se va extrallendo el substring de forma que lo que va quedando al principio siempre debe estar el preceding string.




payload = "#2:643.0605;"

payload_group = []
for group in parsed:
    start= payload.find(group['prec'])+len(group['prec'])
    end= payload.find(group['post'],start)
    print("positions {}:{}".format(start,end))    
    result = payload[start:end]
    payload_group.append(result)
    payload = payload[end:]
    print("Extracted: {} - Remaining: {}".format(result,payload))



pattern = r'[{]'+str(1)+'[}]'
print( re.sub(pattern, "XX", ".00..0..{1}1."))


