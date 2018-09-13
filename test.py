import json
str_js = [('relay1', 12), ('relay2', 15)]
print (str_js)
for relay in str_js:
    print (relay)
    print (relay[0])
    print (relay[1])

js = json.dumps(str_js)
print (type(js))
print (js)
