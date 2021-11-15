import rancher
import logging
import argparse
import pprint
import re
import os
import subprocess
import yaml, string, glob, os
import json
import sys
import requests

name_final = []
cluster_dict = {}
user_dict = {}
data2 = {}
project_dict = {}
#data_bind_cluster = {}
data3 = {}
role_list_dict = {}

def add_user_cluster(client,access_key,secret_key):
    #Read input file
    path = 'groups'
    for filename in glob.glob(os.path.join(path, '*.yaml')):
        with open(os.path.join(os.getcwd(), filename), 'r') as stream:
             out = yaml.load(stream, Loader=yaml.FullLoader)
             users = out['members']
             if 'rancher' in out:
                r_cluster = out['rancher']['cluster']
             else:
                r_cluster = {}
             #print(r_cluster)
        if r_cluster is not None and len(users) != 0:
           for r_cluster_key,r_cluster_value in r_cluster.items():
               for cluster_level_key,cluster_level_value in r_cluster_value.items():
                   if cluster_level_key == 'cluster-level':
                      for cluster_key,cluster_value in cluster_dict.items():
                          if (cluster_key.find(r_cluster_key) != -1):
                             data2['clusterId'] = cluster_value
                             #data2['roleTemplateId'] = groupname[0]
                             for role_id in cluster_level_value:
                                 for role_key,role_val in role_list_dict.items():
                                     if role_val == role_id:
                                        data2['roleTemplateId'] = role_key
                                     else:
                                        data2['roleTemplateId'] = role_id
                                 for i in users:
                                     #print(i)
                                     for key,value in user_dict.items():
                                         if (key.find(i) != -1):
                                            data2['userId'] = value
                                            if "userPrincipalId" in data2.keys():
                                               del data2['userPrincipalId']
                                            if "type" in data2.keys():
                                               del data2['type']
                                            #print(data2)
                                            ret_val = 0
                                            ret_val = list_cluster_bind(client,data2)
                                            if int(ret_val) == 1:
                                               print('create')
                                               api_add_user_cluster(client,data2,access_key,secret_key)
                                            #else:
                                            #   print("no")
                                     if i not in name_final:
                                        data2['userPrincipalId'] = "ping_user://" + i
                                        data2['type'] = "clusterRoleTemplateBinding"
                                        if "userId" in data2.keys():
                                           del data2['userId']
                                        #print(data2)
                                        api_add_user_cluster(client,data2,access_key,secret_key)
                                        list_all_users(client)

def add_user_project(client):
    path = 'groups'
    for filename in glob.glob(os.path.join(path, '*.yaml')):
        with open(os.path.join(os.getcwd(), filename), 'r') as stream:
             out = yaml.load(stream, Loader=yaml.FullLoader)
             project_users = out['members']
             if 'rancher' in out:
                projects_name = out['rancher']['cluster']
             else:
                projects_name = {}
        if projects_name is not None and len(project_users) != 0:
           for projects_name_key,projects_name_value in projects_name.items():
               for pr_name_key,pr_name_value in projects_name_value.items():
                   if pr_name_key != 'cluster-level':
                      for cluster_key,cluster_value in cluster_dict.items():
                          if (cluster_key.find(projects_name_key) != -1):
                             data_project = cluster_value  
                             for project_role_key,project_role_val in project_dict.items():
                                 #if data_project is not None:
                                 lower_val = project_role_val.lower()
                                 if (project_role_key.find(data_project) != -1) and (lower_val.find(pr_name_key) != -1):
                                    data3['projectId'] = project_role_key
                                    for project_role_id in pr_name_value:
                                        for role_key,role_val in role_list_dict.items():
                                            if role_val == project_role_id:
                                               data3['roleTemplateId'] = role_key
                                            else:
                                               data3['roleTemplateId'] = project_role_id
                                        for i in project_users:
                                            for key,value in user_dict.items():
                                                if (key.find(i) != -1):
                                                   data3['userId'] = value
                                                   ret_val_project = 0
                                                   ret_val_project = list_project_bind(client,data3)
                                                   if int(ret_val_project) == 1:
                                                      api_add_user_project(client,data3,access_key,secret_key)


def list_project_bind(client,data3):
    response1 = client.by_id_user(data3['userId'])
    project_data_bind = response1.projectRoleTemplateBindings()
    project_bind_cluster = {}
    project_data_bind1 = project_data_bind['data']
    for project_data_bind2 in project_data_bind1:
        if (project_data_bind2['projectId'].find(data3['projectId']) != -1):
           project_bind_cluster[project_data_bind2['id']] = project_data_bind2['roleTemplateId']
    #print(project_bind_cluster)
    if data3['roleTemplateId'] in project_bind_cluster.values():
       #print("project Role alreday there")
       return('0')
    else:
       print("Create this project role")
       return('1')

def list_role_templates(client,access_key,secret_key):
    url = 'https://rancher.hostname.com/v3/roletemplates'
    res1 = requests.get(url, auth = (access_key,secret_key))
    list_roles = res1.json()
    roles_list = list_roles['data']
    #print(roles_list)
    for role_val in roles_list:
        if not role_val['builtin']:
           role_list_dict[role_val['id']] = role_val['name']

def list_project_name(client):
    #key="harmony_client_url"
    key = "dev_rancher_client_url"

    response1 = client.list_project()
    projects_list = response1['data']
    #print(clusters_list)
    for project_val in projects_list:
        project_dict[project_val['id']] = project_val['name']


def list_all_users(client):

    response1 = client.list_user()
    users_list = response1['data']
    for user_name in users_list:
        user_name1 = user_name['principalIds']
        #print(user_name1)
        name = user_name1[0]
        if len(user_name1) == 2:
           name_id = user_name1[1].split("/")
           name_id_1 = name_id[-1]
           #print(name_id_1)
        if name[0:13] == 'openldap_user' and app_name.lower()=="rancher" and len(user_name1) == 2:
           name_final_1 = name[16:]
           user_dict[name_final_1] = name_id_1
           name_final.append(name_final_1)
           #print(name[16:])
        elif name[0:9] == 'ping_user' and app_name.lower()=="harmony" and len(user_name1) == 2:
           name_final_1 = name[12:]
           user_dict[name_final_1] = name_id_1
           name_final.append(name_final_1)
           #print(name[12:])

def list_cluster_bind(client,data2):
    response1 = client.by_id_user(data2['userId'])
    data_bind = response1.clusterRoleTemplateBindings()
    data_bind_cluster = {}
    data_bind1 = data_bind['data']
    for data_bind2 in data_bind1:
        if (data_bind2['id'].find(data2['clusterId']) != -1):
           data_bind_cluster[data_bind2['id']] = data_bind2['roleTemplateId']
    #print(data_bind_cluster)
    if data2['roleTemplateId'] in data_bind_cluster.values(): 
       #print("Role alreday there")
       return('0')
    else:
       print("Create this role")
       return('1')
    
def list_all_clusters(client):
    #key="harmony_client_url"
    key = "dev_rancher_client_url"

    response1 = client.list_cluster()
    clusters_list = response1['data']
    #print(clusters_list)
    for cluster_id in clusters_list:
        cluster_id_1 = cluster_id['links']
        cluster_id_2 = cluster_id_1['update']
        cluster_id_3 = cluster_id_2.split("/")
        cluster_id_4 = cluster_id_3[-1]
        #print(cluster_id_4)
        cluster_name_1 = cluster_id['name']
        cluster_dict[cluster_name_1] = cluster_id_4
        #print(cluster_name_1)

def api_add_user_cluster(client,data2,access_key,secret_key):
    headers1 = {'Content-Type' : 'application/json'}
    url = 'https://rancher.hostname.com/v3/clusterRoleTemplateBindings'
    res1 = requests.post(url, json=data2, headers=headers1, auth = (access_key,secret_key))
    print (res1.json())

def api_add_user_project(client,data3,access_key,secret_key):
    headers1 = {'Content-Type' : 'application/json'}
    url = 'https://rancher.hostname.com/v3/projectRoleTemplateBindings'
    res1 = requests.post(url, json=data3, headers=headers1, auth = (access_key,secret_key))
    print (res1.json())

def main():
    parser = argparse.ArgumentParser(description="Automated User List Collection Utility")
    #parser.add_argument("-acess_key","-ak", dest="arg1",help="Acess Key")
    #parser.add_argument("-secret_key","-sk", dest="arg2", help="Secret Key")
    args = parser.parse_args()
    global app_name, access_key, secret_key
    #access_key, secret_key=  args.arg1, args.arg2
    access_key = "token-vvkwg"
    secret_key = os.environ.get('RANCHER_TOKEN')
    key = "harmony_client_url"
    app_name = "harmony"
    client = rancher.Client(url='https://rancher.hostname.com/v3',access_key=access_key,secret_key=secret_key,verify=True)
    list_all_clusters(client)
    #print(cluster_dict)
    list_all_users(client)
    #print(user_dict)
    #user_add_cluster(client)
    list_role_templates(client,access_key,secret_key)   
    add_user_cluster(client,access_key,secret_key)
    list_project_name(client)
    #print(data_bind_cluster)
    add_user_project(client)
main()