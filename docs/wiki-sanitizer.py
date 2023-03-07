#!/usr/bin/env python
import os
from configparser import SafeConfigParser

docs_dir = "."
parser = SafeConfigParser()
parser.read("link_mapping")

for dirName, subdirList, fileList in os.walk(os.path.abspath(docs_dir)):
    for name in fileList:
        if name.find(".rst") != -1:
            with open(os.path.join(dirName, name), "r") as f:
                data = f.read()
                for k, v in parser.items("webpages"):
                    if data.find(k) != -1:
                        print("In file, %s, found %s. Replacing with %s" % (name, k, v))
                        data = data.replace(k, v)
                with open(os.path.join(dirName, name), "w") as fd:
                    fd.write(data)
