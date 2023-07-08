import os
import glob
from lxml import etree as ET
import csv
import javalang
import json
import random
import math
import ast
import matplotlib.pyplot as plt

def removeSrcmlTags(srcmlOpt):
    tree = ET.fromstring(srcmlOpt)
    text_nodes = tree.xpath("//text()")
    source_code = "".join(text for text in text_nodes)
    return source_code

def extract_method_srcml_inheritance(file_path, class_name, method_name):
    srcml_output = os.path.splitext(file_path)[0] + ".xml"
    os.system(f"srcml {file_path} -o {srcml_output}")    
    with open(srcml_output, "rb") as file:
        srcml_output = file.read()
    tree = ET.fromstring(srcml_output)
    namespace = {'src': 'http://www.srcML.org/srcML/src'}
    class_elements = tree.xpath(f'//src:class[src:name="{class_name}"]', namespaces=namespace)
    if not class_elements:
        print(f"No class named '{class_name}' found.")
        return None
    class_element = class_elements[0]
    method_elements = class_element.xpath(f'.//src:function[src:name="{method_name}"]', namespaces=namespace)
    if method_elements:
        code_block = ET.tostring(method_elements[0], encoding='unicode', with_tail=False).strip()
        code_block = removeSrcmlTags(code_block)
        return code_block
    extends_elements = class_element.xpath('.//src:super_list/src:extends', namespaces=namespace)
    if extends_elements:
        parent_class_name = extends_elements[0].xpath('.//src:name', namespaces=namespace)[0].text
        return extract_method_srcml_inheritance(file_path, parent_class_name, method_name)
    else:
        print(f"Method '{method_name}' not found in class '{class_name}' or any parent classes.")
        return None

def extract_method_srcml_no_inheritance(file_path, method_name):
    srcml_output = os.path.splitext(file_path)[0] + ".xml"
    os.system(f"srcml {file_path} -o {srcml_output}")    
    with open(srcml_output, "rb") as file:
        srcml_output = file.read()
    tree = ET.fromstring(srcml_output)
    namespace = {'src': 'http://www.srcML.org/srcML/src'}
    method_element = tree.xpath(f'//src:function[src:name="{method_name}"]', namespaces=namespace)[0]
    code_block = ET.tostring(method_element, encoding='unicode', with_tail=False).strip()
    code_block = removeSrcmlTags(code_block)    
    return code_block

def readCSV(input_file, headers=False):
    with open(input_file, 'r') as csvfile:
        reader = csv.reader(csvfile)
        csv_data = [row for row in reader]
        if headers:
            csv_data.pop(0)
    return csv_data

def list_java_files(directory):
    path = os.path.join(directory, '**', '*.java')
    java_files = glob.glob(path, recursive=True)
    return java_files

def getProjName(url):
    parts = url.split('/')
    project_name = parts[-1].split('.')[0]
    return project_name

def createCSV(csv_file,data):
    with open(csv_file, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        for row in data:
            writer.writerow(row)

def writeFile(fileName,content):
    with open(fileName, 'w', encoding='utf-8') as f:
        f.write(content)

def appendFile(fileName,content):
    with open(fileName, 'a', encoding='utf-8') as f:
        f.write(content+"\n")

def mkdir(path):
    if not os.path.exists(path):
        os.makedirs(path)  

def generate_random_lists(input_list,start=5,end=1000,step=5):
    output = {}
    for i in range(start, min(len(input_list), end+1), step):
        output[i] = random.sample(input_list, k=i)    
    return output

def readFile(fileName):
    with open(fileName, 'r') as file:
        contents = file.read()
    return contents

def generateProcessedOrgCsv(csv_data):
    csv_data = [["gitURL","sha","module","victim","polluter","cleaner","type","victim_code","polluter_code","cleaner_code"]] + csv_data
    fileName = os.path.join("output","processedOrgCsv.csv")
    createCSV(fileName,csv_data)

def getGitURL(url):
    if not url.endswith(".git"):
        url=url+".git"
    return url

def getModule(module):
    if module.startswith("."):
        module=module[1:]
    if module.startswith("/"):
        module=module[1:]
    if module=="":
        return "NA"
    else:
        return module

def createData(csv_data):
    data={}
    i=1
    for row in csv_data:
        print("Processing row: "+str(i))
        git=row[0]
        if not git.endswith(".git"):
            git=git+".git"
        if git not in data.keys():
            data[git]={}
        sha=row[1]
        data[git]["sha"]=sha
        module=row[2]
        if module.startswith("."):
            module=module[1:]
        if module.startswith("/"):
            module=module[1:]
        if module == "":
            module="NA"
        if module not in data[git].keys():
            data[git][module]={}
            data[git][module]["methods"]=set()
            data[git][module]["polluters"]={}
            data[git][module]["cleaners"]={}
            data[git][module]["victims"]=set()
            data[git][module]["brittles"]=set()
            data[git][module]["statesetters"]={}
        if row[6]=="victim":        
            victim=row[3]
            polluter=row[4]
            cleaner=row[5]
            if victim != "":
                data[git][module]["methods"].add(victim)
                data[git][module]["victims"].add(victim)
            if polluter != "":
                data[git][module]["methods"].add(polluter)
                if victim not in data[git][module]["polluters"].keys():
                    data[git][module]["polluters"][victim]=set()
                data[git][module]["polluters"][victim].add(polluter)
            if cleaner != "":
                data[git][module]["methods"].add(cleaner)
                if victim not in data[git][module]["cleaners"].keys():
                    data[git][module]["cleaners"][victim]={}
                if polluter not in data[git][module]["cleaners"][victim].keys():
                    data[git][module]["cleaners"][victim][polluter]=set()
                data[git][module]["cleaners"][victim][polluter].add(cleaner)
        elif row[6]=="brittle":
            brittle=row[3]
            statesetter=row[4]
            if brittle!="":
                data[git][module]["methods"].add(brittle)
                data[git][module]["brittles"].add(brittle)
            if statesetter!="":
                data[git][module]["methods"].add(statesetter)
                if brittle not in data[git][module]["statesetters"].keys():
                    data[git][module]["statesetters"][brittle]=set()
                data[git][module]["statesetters"][brittle].add(statesetter)
        else:
            appendFile("log.txt","Failed to process row: "+str(i))
        print("Completed processing row: "+str(i))
        i=i+1
    return data

def getVpcbssData():
    with open('vpcbss_dataset.txt', 'r') as f:
        dict_string = f.read()
        my_dict = ast.literal_eval(dict_string)
    return my_dict

def createMethData(methodOrders):
    data={}
    for row in methodOrders:
        git=row[0]
        sha=row[1]
        module=getModule(row[2])
        orderLen=row[3]
        orderFileName=row[4]
        orders=readFile("input/"+orderFileName)
        if git not in data.keys():
            data[git]={
                "sha":sha
            }
        if module not in data[git].keys():
            data[git][module]={}
        #data[git][module][orderLen]=orderFileName
        data[git][module][orderLen]=getOrders(orders)
    return data

def getOrders(ordersStr):
    orders=[]
    ordersStr=ordersStr.split("|")
    for order in ordersStr:
        orders.append(order.split(":"))
    return orders


def createMethData4c2mon(methodOrders):
    data={}
    for row in methodOrders:
        git=row[0]
        if git.endswith("c2mon.git"):
            sha=row[1]
            module=getModule(row[2])
            orderLen=row[3]
            orderFileName=row[4]
            orders=readFile("input/"+orderFileName)
            if git not in data.keys():
                data[git]={
                    "sha":sha
                }
            if module not in data[git].keys():
                data[git][module]={}
            #data[git][module][orderLen]=orderFileName
            data[git][module][orderLen]=getOrders(orders)
    return data

def plotGraph(x_values,y_values,title):
    plt.plot(x_values, y_values)
    plt.title(title)
    plt.xlabel('X values')
    plt.ylabel('Y values')
    plt.savefig("output/"+title.replace(" ","_")+'.png', format='png')
    plt.close()

def generateXYValues4c2mon(git,module,orders,vpcbss_data):
    victim=list(vpcbss_data[git][module]["victims"])[0]
    polluter=list(vpcbss_data[git][module]["polluters"][victim])[0]
    x=[]
    y=[]
    i=1
    for order in orders:
        y.append(order.index(polluter))
        x.append(i)
        i+=1
    return x,y

def generateGraphs4c2mon(methodOrders_data,vpcbss_data):
    for git in methodOrders_data.keys():
        for module in methodOrders_data[git].keys():
            if module!="sha":
                for orderLen in methodOrders_data[git][module].keys():
                    orders=methodOrders_data[git][module][orderLen]
                    x,y=generateXYValues4c2mon(git,module,orders,vpcbss_data)
                    plotGraph(x,y,orderLen+" orders")
                        

if __name__ == "__main__":
    mkdir("output")
    vpcbss_data=getVpcbssData()
    methodOrders_csv=readCSV("methodOrders.csv",True)
    #methodOrders_data=createMethData(methodOrders_csv)
    methodOrders_data=createMethData4c2mon(methodOrders_csv)
    generateGraphs4c2mon(methodOrders_data,vpcbss_data)
    
