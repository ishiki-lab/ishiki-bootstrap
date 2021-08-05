import requests
from requests.structures import CaseInsensitiveDict
import datetime
from os import listdir, system, environ
from dotenv import load_dotenv
import pprint
import logging
from pyportainer import *

pp = pprint.PrettyPrinter(indent=4)

PORTAINER_URL = "https://gateways.bos.arupiot.com"
API_URL = "/api"

# get environment variables from .env file
load_dotenv()

if environ['PORTAINER_USERNAME'] != '':
    PORTAINER_USERNAME = environ['PORTAINER_USERNAME']
else:
    PORTAINER_USERNAME = 'admin'

if environ['PORTAINER_PASSWORD'] != '':
    PORTAINER_PASSWORD = environ['PORTAINER_PASSWORD']
else:
    PORTAINER_PASSWORD = 'password'


# authenticate
def portainer_authenticate(portainer_url, portainer_username, portainer_password):
    # http POST <portainer url>/api/users/admin/init Username="<admin username>" Password="<adminpassword>"
    data = {
            "Username": portainer_username,
            "Password": portainer_password
    }
    logging.info("authenticating")
    #print(data)
    rsp = requests.post(portainer_url+"/auth", json=data)

    #print(dir(rsp))
    print(rsp.headers)
    # print(rsp.json)
    access_token = ""

    if rsp.status_code == 200:
        result = rsp.json()
        access_token = result["jwt"]
        # print(access_token)
    else:
        raise Exception("not authorised")
    return access_token

# list endpoints
def portainer_list_endpoints(portainer_url, access_token):
    # http --form GET <portainer url/api/endpoints "Authorization: Bearer <jwt token>" 

    data = {
    }

    # headers = {
    #     'Authorization':'Bearer %s' % access_token
    # }

    headers = CaseInsensitiveDict()
    headers["Accept"] = 'application/json'
    headers["Authorization"] = 'Bearer %s' % access_token

    #print(headers)
    # pp.pprint(headers)

    rsp = requests.get(portainer_url+"/endpoints", headers=headers)
    # pp.pprint(rsp.headers)
    # pp.pprint(rsp.json())
    return(rsp.json())

# list endpoints
def portainer_get_endpoint(portainer_url, access_token, id):
    # http --form GET <portainer url/api/endpoints "Authorization: Bearer <jwt token>" 

    data = {
    }

    # headers = {
    #     'Authorization':'Bearer %s' % access_token
    # }

    headers = CaseInsensitiveDict()
    headers["Accept"] = 'application/json'
    headers["Authorization"] = 'Bearer %s' % access_token

    #print(headers)
    # pp.pprint(headers)

    rsp = requests.get(portainer_url+"/endpoints/%s" % id, headers=headers)
    # pp.pprint(rsp.headers)
    # pp.pprint(rsp.json())
    return(rsp.json())

# list stacks
def portainer_list_stacks(portainer_url, access_token):
    # http --form GET <portainer url/api/stacks "Authorization: Bearer <jwt token>" 

    data = {
    }

    # headers = {
    #     'Authorization':'Bearer %s' % access_token
    # }

    headers = CaseInsensitiveDict()
    headers["Accept"] = 'application/json'
    headers["Authorization"] = 'Bearer %s' % access_token

    #print(headers)
    # pp.pprint(headers)

    rsp = requests.get(portainer_url+"/stacks", headers=headers)
    # pp.pprint(rsp.headers)
    # pp.pprint(rsp.json())
    return(rsp.json())

def portainer_list_endpoint_stacks(portainer_url, access_token, endpoint_id):
    # http --form GET <portainer url/api/stacks "Authorization: Bearer <jwt token>" 

    data = {
    }

    # headers = {
    #     'Authorization':'Bearer %s' % access_token
    # }

    headers = CaseInsensitiveDict()
    headers["Accept"] = 'application/json'
    headers["Authorization"] = 'Bearer %s' % access_token

    #print(headers)
    # pp.pprint(headers)

    rsp = requests.get(portainer_url+"/endpoints/%s/edge/stacks/1" % endpoint_id, headers=headers)
    # pp.pprint(rsp.headers)
    # pp.pprint(rsp.json())
    return(rsp.json())


# create endpoint
def portainer_create_endpoint(portainer_url, access_token, endpoint_name, endpoint_creation_type, url):
    # http --form POST <portainer url/api/endpoints "Authorization: Bearer <jwt token>" Name="<endpoint name>" EndpointCreationType=1

    headers = CaseInsensitiveDict()
    headers["Accept"] = 'application/json'
    headers["Authorization"] = 'Bearer %s' % access_token

    data = {
        "Name": endpoint_name,
        "EndpointCreationType": endpoint_creation_type,
        "URL": url
    }

    rsp = requests.post(portainer_url+"/endpoints", headers=headers, data=data)

    pp.pprint(rsp.headers)
    pp.pprint(rsp.json())


def main():

    print("not using PyPortainer")
    portainer_url = PORTAINER_URL + API_URL
    token = portainer_authenticate(portainer_url, PORTAINER_USERNAME, PORTAINER_PASSWORD)
    endpoints = portainer_list_endpoints(portainer_url, token)
    # pp.pprint(endpoints)
    for endpoint in endpoints:
        print()
        print(endpoint.get("Name"), endpoint.get("EdgeID"), endpoint.get("EdgeKey"),)
        id = int(endpoint.get("Id"))
        edge_id = endpoint.get("EdgeID")
        ep = portainer_get_endpoint(portainer_url, token, id)
        pp.pprint(ep)
        # print()
        stacks = portainer_list_endpoint_stacks(portainer_url, token, id)
        pp.pprint(stacks)
        print()

    # create endpoints
    # portainer_create_endpoint(portainer_url, token, "test0", 0)
    # portainer_create_endpoint(portainer_url, token, "test1", 1)
    # portainer_create_endpoint(portainer_url, token, "test2", 2)
    # portainer_create_endpoint(portainer_url, token, "test3", 3)
    portainer_create_endpoint(portainer_url, token, "test1", 4, "https://gateways.bos.arupiot.com")



    # stacks = portainer_list_stacks(portainer_url, token)
    # for stack in stacks:
    #     pp.pprint(stack)
    # pp.pprint(stacks)


    # print()
    # print("using PyPortainer")

    # # instance the PyPortainer class
    # p = PyPortainer(PORTAINER_URL)
    # # authenticate the PyPortainer instance
    # p.login(PORTAINER_USERNAME, PORTAINER_PASSWORD)
    
    # endpoints = p.get_endpoints()
    # for e in endpoints:
    #     id = int(e.get("Id"))
    #     print(e.get("Name"), e.get("Id"), e.get("EdgeID"), e.get("EdgeKey"))
    #     pp.pprint(e)
    #     print()
    #     # get stacks for this endpoint
    #     # try:
    #     stacks = p.get_stacks(id)
    #     for s in stacks:
    #         # print(s.get("Name"), s.get("Env"), p.get_stackfile(1,s.get("Id"))["StackFileContent"])
    #         print(s.get("Name"))
    #     # except:
    #     #     print("no stacks")


if __name__ == '__main__':
    main()