"""
Created on: 12/10/2024 18:49

Authors: Shyam Bhuller (University of Oxford), Matthew Man (University of Toronto), Danaisis Vargas Oliva (University of Toronto)

Description: Module to handle queries to the grafana dahsboards through the grafana HTTP api.
"""
import json
from warnings import warn

from urllib.parse import urljoin, urlencode
from urllib.request import urlopen
from urllib.error import URLError, HTTPError
from http.client import HTTPResponse

import aiohttp
import utils

from times import time_range

from rich import print


async def arequest(session : aiohttp.ClientSession, url : str, extension : str = None, params : dict[str] = None):
    try:
        full_url = urljoin(url, extension)
        async with aiohttp.ClientSession() as session:
            async with session.get(full_url, params = params) as resp:
                data = await resp.json()
        if resp.status != 200:
            print(f"Request for {full_url} got respone {resp.status}, {data}")
    except Exception as e:
        print(e)
    return data


def request(url : str, extension : str, data : dict = None) -> dict | None:
    """ Make a http request.

    Args:
        url (str): http url
        extension (str): url extension, such as a query.
        data (dict, optional): data to pass if the exentsion takes data as input. Defaults to None.

    Returns:
        dict | None: http repsonse.
    """
    response_data = None
    try: # attempt to make the query, and stop if it is successful
        with urlopen(urljoin(url, extension), data = urlencode(data).encode() if data else None) as response:
            if response.status == 200:
                response_data = urljson(response)
    except (HTTPError, URLError, ValueError) as e:
        print(f"request {urljoin(url, extension)}, {data} could not be made: {e}")

    return response_data


async def aquery_prometheus(cs : aiohttp.ClientSession, url : str, query_str : str, time_range : time_range) -> dict | None:
    data = {
        'query': query_str,
        'start': time_range.start,
        'end': time_range.end,
        'step': 2 # make this configurable?
    }
    return arequest(cs, url, "api/v1/query_range", data)


def query_prometheus(url : str, query_str : str, time_range : time_range) -> dict | None:
    """ Make a query from a prometheus database.
        Authors: Shyam Bhuller (University of Oxford), Matthew Man (University of Toronto), Danaisis Vargas Oliva (University of Toronto)

    Args:
        url (str): datasource url.
        query_str (str): query to make.
        time_range (time_range): time range to make query in.

    Returns:
        dict | None: http response
    """
    data = {
        'query': query_str,
        'start': time_range.start,
        'end': time_range.end,
        'step': 2 # make this configurable?
    }
    return request(url, "api/v1/query_range", data)


def make_names_str(names : list) -> str:
    """ Convert a list of values into a format compatible for InfluxDB query strings.
        Authors: Shyam Bhuller (University of Oxford)

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


async def aget_datasources(cs : aiohttp.ClientSession, url : str) -> list[dict]:
    return arequest(cs, url, "api/datasources")


def get_datasources(url : str) -> list[dict]:
    """ Get the urls for each datasource the Grafana dashboards use.
        Authors: Shyam Bhuller (University of Oxford), Matthew Man (University of Toronto), Danaisis Vargas Oliva (University of Toronto)

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


async def get_grafana_panels(cs : aiohttp.ClientSession, url : str, uid : str):
    panels = []
    # Get dashboard configuration
    out = arequest(cs, urljoin(url, f"api/dashboards/uid/{uid}"))
    if out is None:
        return []
    else:
        return out


def get_grafana_panels(url : str, uid : str) -> list[dict]:
    """ Get panels from a grafana dashboard.
        Authors: Shyam Bhuller (University of Oxford), Matthew Man (University of Toronto), Danaisis Vargas Oliva (University of Toronto)

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
        Authors: Shyam Bhuller (University of Oxford), Matthew Man (University of Toronto), Danaisis Vargas Oliva (University of Toronto)

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
        Authors: Shyam Bhuller (University of Oxford)

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
            if len(targets) > 1:
                name = target["alias"]
            else:
                name = panel["title"]
            queries[name] = target["query"]
        elif 'rawSql' in target:
            print(target)
            queries[target["table"]] = target["rawSql"]

    return queries


async def amake_query(cs : aiohttp.ClientSession, datasource : dict, url : str, query : str, time : time_range) -> dict | None:
    response_data = None

    url_extension = "query" # extension to make queries from the api
    if datasource["type"] == "influxdb":
        # data for influxdb v1
        data = {
            "q" : query,
            "db" : datasource["jsonData"]["dbName"]
        }
    elif datasource["type"] == "prometheus":
        # data for prometheus
        data = {
            'query': query,
            'start': time.start,
            'end': time.end,
            'step': 2 # make this configurable?
        }
        url_extension = "api/v1/query_range"
    elif datasource["type"] == "postgres":
        #! not 100% if this is correct.
        data = {
            "query" : query,
        }
    else:
        warn(f"unknown database type: {datasource['type']}")
        return response_data

    response_data = arequest(cs, url, f"api/datasources/proxy/uid/{datasource['uid']}/{url_extension}", data) # attempt to make the query, and stop if it is successful
    return response_data


def make_query(datasource : dict, url : str, query : str, time : time_range) -> dict | None:
    """ Query from the grafana dashboard, and return the data if the query is successful.
        Authors: Shyam Bhuller (University of Oxford), Matthew Man (University of Toronto), Danaisis Vargas Oliva (University of Toronto)

    Args:
        datasource (dict): datasource to query from.
        url (str): Grafana url to make the query through.
        query (str): query string.
        time (time_range): time range to make the query within (required for Prometheus queries, but not InfluxDB as the string contains the time range).

    Returns:
        dict | None: data from the response if the query was successful or None if the query fails.
    """
    response_data = None

    url_extension = "query" # extension to make queries from the api
    if datasource["type"] == "influxdb":
        # data for influxdb v1
        data = {
            "q" : query,
            "db" : datasource["jsonData"]["dbName"]
        }
    elif datasource["type"] == "prometheus":
        # data for prometheus
        data = {
            'query': query,
            'start': time.start,
            'end': time.end,
            'step': 2 # make this configurable?
        }
        url_extension = "api/v1/query_range"
    elif datasource["type"] == "postgres":
        #! not 100% if this is correct.
        data = {
            "query" : query,
        }
    else:
        warn(f"unknown database type: {datasource['type']}")
        return response_data

    response_data = request(url, f"api/datasources/proxy/uid/{datasource['uid']}/{url_extension}", data) # attempt to make the query, and stop if it is successful
    return response_data


def search_panel(d, action : callable, args : dict) -> dict:
    """ Recusrively search for each value in the panel, and perform a function on the value. Panel passed is modified.
        Authors: Shyam Bhuller (University of Oxford)

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
        Authors: Shyam Bhuller (University of Oxford)

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


async def aquery_var_influx(cs : aiohttp.ClientSession, url : str, datasource : dict, query_str : str) -> dict | None:
    data = {
        "q"  : query_str,
        "db" : datasource["jsonData"]["dbName"]
    } 
    return arequest(cs, url, f"api/datasources/proxy/uid/{datasource['uid']}/query", data)


def query_var_influx(url : str, datasource : dict, query_str : str) -> dict | None:
    """ Query from specifically the opmon influxdb datasource used for the daq applications.
        Authors: Shyam Bhuller (University of Oxford)

    Args:
        url (str): Grafana url.
        datasources (dict): influx datasource.
        query_str (str): Query string.
        ds_id (int) : dashboard id

    Returns:
        dict | None: data from the response if successful, otherwise None.
    """
    data = {
        "q"  : query_str,
        "db" : datasource["jsonData"]["dbName"]
    }
    try:
        with urlopen(urljoin(url, f"api/datasources/proxy/uid/{datasource['uid']}/query"), urlencode(data).encode()) as response:
            return urljson(response)
    except HTTPError as e:
        print(e)
    return


def extract_vars(query_str : str) -> list[str]:
    """ Extract all variable names from a query string.
        Authors: Shyam Bhuller (University of Oxford)

    Args:
        query_str (str): Query string.

    Returns:
        list[str]: list of all variable names.
    """
    v = []
    for i in query_str.split("$")[1:]: # first part doesnt matter
        v.append(i.split(" ")[0].replace("{", "").replace("}", "").replace("'", "").replace("/", "")) # this is ugly
    return v
