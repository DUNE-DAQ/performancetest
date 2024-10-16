"""
Created on: 12/10/2024 18:49

Author: Shyam Bhuller

Description: Module to handle queries to the grafana dahsboards through the grafana HTTP api.
"""
import json
from warnings import warn

from collections import namedtuple

from urllib.parse import urljoin, urlencode
from urllib.request import urlopen
from urllib.error import URLError, HTTPError
from http.client import HTTPResponse

import utils

from rich import print

time_range = namedtuple("time_range", ["start", "end"])


def request():
    #! make function to make a generic http request with exception handling.
    return


def make_names_str(names : list) -> str:
    """ Convert a list of values into a format compatible for InfluxDB query strings.

    Args:
        names (list): list of values

    Returns:
        str: Formatted list.
    """
    names_str = "("
    for i, n in enumerate(names):
        if i == (len(names) - 1):
            names_str += f"{n})"
        else:
            names_str += f"{n}|"

    return names_str


def get_datasources(url : str) -> list[dict]:
    """ Get the urls for each datasource the Grafana dashboards use.

    Args:
        url (str): Grafana url.

    Raises:
        Exception: Error in making the http request.

    Returns:
        list[dict]: list of each datasource used.
    """
    with urlopen(urljoin(url, "api/datasources")) as response:
        if response.status == 200:
            return urljson(response)
        else:
            raise Exception(f"http request resulted in code: {response.status_code}")


def get_grafana_panels(url : str, uid : str) -> list[dict]:
    """ Get panels from a grafana dashboard.

    Args:
        grafana_url (str): Grafana url.
        dashboard_uid (str): Dashboard uid.

    Returns:
        list[dict]: List of each panel on the dashboard containing information required to make queries.
    """
    panels = []
    # Get dashboard configuration
    dashboard_url = urljoin(url, f"api/dashboards/uid/{uid}")

    with urlopen(dashboard_url) as response:
        try:
            if response.status == 200:
                panels = urljson(response)['dashboard']['panels'] # Extract panels data
                return panels
        except HTTPError as e:
            print('Error code: ', e.code)
        except URLError as e:
            print('Reason: ', e.reason)


def urljson(response : HTTPResponse) -> dict | None:
    """ Attempt to decode http content in json format.

    Args:
        response (HTTPResponse): http response.

    Returns:
        dict | None: Dictionary of json, or None if content type does not match.
    """
    content_type = response.headers.get('Content-Type')
    if content_type == 'application/json':
        return json.loads(response.read())
    else:
        print(f'Warning: Response is not in JSON format. Content-Type: {content_type}')


def get_queries(panel : dict) -> dict:
    """ Return each query made by the panel.

    Args:
        panel (dict): Grafana panel.

    Returns:
        dict: query along with its name/description.
    """

    targets = panel.get('targets', [])
    queries = {}

    for target in targets:
        if ('expr' in target) and (target["expr"] != ""):
            queries[target["legendFormat"]] = target["expr"]
        elif 'query' in target:
            queries[panel["title"]] = target["query"]
        elif 'rawSql' in target:
            print(target)
            queries[target["table"]] = target["rawSql"]

    return queries


def make_query(datasources : list[dict], url : str, query : str, time : time_range) -> dict | None:
    """ Query from the grafana dashboard, and return the data if the query is successful.

    Args:
        datasources (list[dict]): datasources to make the queries to.
        url (str): Grafana url to make the queries through.
        query (str): query string.
        time (str): time range to make the query within (required for Prometheus queries, but not InfluxDB as the string contains the time range).

    Returns:
        dict | None: data from the response if the query was successful or None if the query fails.
    """
    response_data = None
    error = None # error message
    for i in datasources: # loop through all data sources and attempt the query #! this can be improved as the panel information should contain the datasource type
        if i["name"] in ["CERN IT Networking SNMP", "KluPrometheus"]: continue # These datasources do not contain any information from the run

        url_extension = "query" # extension to make queries from the api
        if i["type"] == "influxdb": # Check the datasource type and populate the data required for the query appropriately.
            # data for influxdb v1
            data = {
                "q" : query,
                "db" : i["jsonData"]["dbName"]
            }
        elif i["type"] == "prometheus":
            # data for prometheus
            data = {
                'query': query,
                'start': time.start,
                'end': time.end,
                'step': 2 # make this configurable?
            }
            url_extension = "api/v1/query_range"
        elif i["type"] == "postgres":
            #! not 100% if this is correct.
            data = {
                "query" : query,
            }
        else:
            warn(f"unknown database type: {i['type']}")
            continue

        try: # attempt to make the query, and stop if it is successful
            with urlopen(urljoin(url, f"api/datasources/proxy/uid/{i['uid']}/{url_extension}"), urlencode(data).encode()) as response:
                if response.status == 200:
                    response_data = urljson(response)
                    break
        except (HTTPError, URLError, ValueError) as e:
            error = e
            pass

    if not response_data:
        print(f"query could not be made to any database: {error}")

    return response_data


def search_panel(d, action : callable, args : dict) -> dict:
    """ Recusrively search for each value in the panel, and perform a function on the value. Panel passed is modified.

    Args:
        d: the panel or an element in the panel.
        action (callable): function to apply to the values found. 
        args (dict): arguments for the action.

    Returns:
        dict: panel or the modified information.
    """ 
    if (type(d) == dict) and utils.is_collection(d): # specific rule to iterate through a dictionary
        #? is there a way to iterate dictionaries and lists/arrays in the same way?
        for k in d:

            if k == "datasource" : d[k]["uid"] = None # we need to try each uid

            if utils.is_collection(d): # if the value from the key is a collection, call search_panel again
                new = search_panel(d[k], action, args)
                d[k] = new # append 
    elif utils.is_collection(d):
        for i in range(len(d)):
            if utils.is_collection(d[i]):
                new = search_panel(d[i], action, args)
                d[i] = new
    else:
        return action(d, **args)
    return d


def replace_var(query : str, target : str, value : str) -> str:
    """ Replace variable in query string if exists. 

    Args:
        query (any): Query string.
        target (str): Target to replace.
        value (any): Value to replace it with.

    Returns:
        str: query string.
    """
    if type(query) != str: return query

    if target in query:
        query = query.replace(f"${{{target}}}", value)
        query = query.replace(f"${target}", value)
    return query


def query_var(url : str, datasources : list[dict], query_str : str) -> dict | None:
    """ Query from specifically the opmon influxdb datasource used for the daq applications.

    Args:
        url (str): Grafana url.
        datasources (list[dict]): List of datasources.
        query_str (str): Query string.

    Returns:
        dict | None: data from the response if successful, otherwise None.
    """
    for i in datasources:
        if i["id"] != 11: continue
        data = {
            "q" : query_str,
            "db" : i["jsonData"]["dbName"]
        }
        try:
            with urlopen(urljoin(url, f"api/datasources/proxy/uid/{i['uid']}/query"), urlencode(data).encode()) as response:
                return urljson(response)
        except HTTPError as e:
            print(e)
    return


def extract_vars(query_str : str) -> list[str]:
    """ Extract all variable names from a query string.

    Args:
        query_str (str): Query string.

    Returns:
        list[str]: list of all variable names.
    """
    v = []
    for i in query_str.split("$")[1:]: # first part doesnt matter
        v.append(i.split(" ")[0].replace("{", "").replace("}", "").replace("'", "").replace("/", "")) # this is ugly
    return v
