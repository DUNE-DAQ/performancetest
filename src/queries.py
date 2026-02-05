"""
Created on: 12/10/2024 18:49

Authors: Shyam Bhuller (University of Oxford), Matthew Man (University of Toronto), Danaisis Vargas Oliva (University of Toronto)

Description: Module to handle queries to the grafana dahsboards through the grafana HTTP api.
"""
import asyncio
from warnings import warn

from urllib.parse import urljoin

import aiohttp

import utils

from times import time_range

from rich import print


async def request(session : aiohttp.ClientSession, style : str, url : str, extension : str = None, params : dict[str] = None, json : dict = None) -> dict | None:
    """ Make a http request.

    Args:
        session (aiohttp.ClientSession): Open ClientSession from which to make the http request.
        style (str): type of request to make, either "get" or "set".
        url (str): http url
        extension (str): url extension, such as a query.
        params (dict[str], optional): Parameters to pass if the extension takes data as input. Defaults to None.
        json (dict, optional): json complient data to pass to the query. Defaults to None.

    Returns:
        dict | None: http repsonse.
    """
    func = getattr(session, style)
    data = None
    try:
        full_url = urljoin(url, extension)
        async with func(full_url, json = json, params = params) as resp:
            data = await resp.json()
        if resp.status != 200:
            print(f"Request for {full_url} got respone {resp.status}, {data},\nparameters sent were: {params}")
            data = None
    except Exception as e:
        print(e)
    return data


def get_request(session : aiohttp.ClientSession, url : str, extension : str = None, params : dict[str] = None, json : dict = None) -> dict | None:
    """ Make a get request

    Args:
        session (aiohttp.ClientSession): Open ClientSession from which to make the http request.
        url (str): http url
        extension (str): url extension, such as a query.
        params (dict[str], optional): Parameters to pass if the extension takes data as input. Defaults to None.
        json (dict, optional): json complient data to pass to the query. Defaults to None.

    Returns:
        dict | None: http repsonse.
    """
    return request(session, "get", url, extension, params, json)


def post_request(session : aiohttp.ClientSession, url : str, extension : str = None, params : dict[str] = None, json : dict = None) -> dict | None:
    """ Make a post request.

    Args:
        session (aiohttp.ClientSession): Open ClientSession from which to make the http request.
        url (str): http url
        extension (str): url extension, such as a query.
        params (dict[str], optional): Parameters to pass if the extension takes data as input. Defaults to None.
        json (dict, optional): json complient data to pass to the query. Defaults to None.

    Returns:
        dict | None: http repsonse.
    """
    return request(session, "post", url, extension, params, json)


def query_prometheus(cs : aiohttp.ClientSession, url : str, datasource : dict, query_str : str, time_range : time_range, direct : bool = False) -> dict | None:
    """ Make a query from a prometheus database.
        Authors: Shyam Bhuller (University of Oxford), Matthew Man (University of Toronto), Danaisis Vargas Oliva (University of Toronto)

    Args:
        cs (aiohttp.ClientSession): Open ClientSession from which to make the http request.
        url (str): Datasource url.
        query_str (str): Query to make.
        time_range (time_range): Time range to make query in.
        direct (bool): set to true to directly query through, prometheus otherwise query through the grafana proxy. Defaults to False

    Returns:
        dict | None: http response
    """
    auto_step = 1 + int((time_range.end - time_range.start) / 11000) # maximum number of data points in a query is 11,000
    data = {
        'query': query_str,
        'start': time_range.start,
        'end': time_range.end,
        'step': auto_step
    }

    extension = "api/v1/query_range"
    if not direct:
        extension = f"api/datasources/proxy/uid/{datasource['uid']}/" + extension # if using the grafana proxy
    return get_request(cs, url, extension, params = data)


def query_influx(cs : aiohttp.ClientSession, url : str, datasource : dict, query_str : str) -> dict | None:
    """ Query from specifically the opmon influxdb datasource used for the daq applications.
        Authors: Shyam Bhuller (University of Oxford)

    Args:
        cs (aiohttp.ClientSession): Open ClientSession from which to make the http request.
        url (str): Grafana url.
        datasources (dict): Influx datasource.
        query_str (str): Query string.
        ds_id (int) : Dashboard id.

    Returns:
        dict | None: data from the response if successful, otherwise None.
    """
    data = {
        "q"  : query_str,
        "db" : datasource["jsonData"]["dbName"]
    } 
    return get_request(cs, url, f"api/datasources/proxy/uid/{datasource['uid']}/query", data)


def query_postgres(cs : aiohttp.ClientSession, url : str, datasource : dict, query : str, time : time_range) -> dict | None:
    str_time = time_range(start = str(time.start) + "000", end = str(time.end) + "000") # need higher precision times for postgres queries.
    payload = {
        "from" : str_time.start,
        "to" : str_time.end,
        "queries" : [
            {
                "refId" : "host",
                "datasource" : {
                    "type" : "postgres",
                    "uid" : datasource["uid"]
                },
                "rawSql" : query.replace(str(time.start), str_time.start).replace(str(time.end), str_time.end),
                "format" : "table"
            }
        ]
    }
    return post_request(cs, url, "/api/ds/query", json = payload)


async def make_query(cs : aiohttp.ClientSession, datasource : dict, url : str, query : str, time : time_range) -> dict | None:
    """ Query from the grafana dashboard, and return the data if the query is successful.
        Authors: Shyam Bhuller (University of Oxford), Matthew Man (University of Toronto), Danaisis Vargas Oliva (University of Toronto)

    Args:
        cs (aiohttp.ClientSession): Open ClientSession from which to make the http request.
        datasource (dict): Datasource to query from.
        url (str): Grafana url to make the query through.
        query (str): Query string.
        time (time_range): Time range to make the query within (required for Prometheus queries, but not InfluxDB as the string contains the time range).

    Returns:
        dict | None: data from the response if the query was successful or None if the query fails.
    """
    response_data = None

    if datasource["typeName"] == "InfluxDB":
        # data for influxdb v1
        response_data = await query_influx(cs, url, datasource, query)
    elif datasource["typeName"] == "Prometheus":
        # data for prometheus
        response_data = await query_prometheus(cs, url, datasource, query, time)
    elif datasource["typeName"] == "PostgreSQL":
        response_data = await query_postgres(cs, url, datasource, query, time)
    else:
        warn(f"unknown database type: {datasource['typeName']}")

    return response_data


async def get_grafana_panels(cs : aiohttp.ClientSession, url : str, uid : str) -> list[dict]:
    """ Get panels from a grafana dashboard.
        Authors: Shyam Bhuller (University of Oxford)

    Args:
        cs (aiohttp.ClientSession): Open ClientSession from which to make the http request.
        url (str): Grafana url.
        uid (str): Dashboard uid.

    Returns:
        list[dict]: List of each panel on the dashboard containing information required to make queries.
    """
    panels = await get_request(cs, urljoin(url, f"api/dashboards/uid/{uid}"))
    return panels['dashboard']['panels'] # Extract panels data


def aquery_single(func : callable, **kwargs) -> any:
    """ Make a single async query.

    Args:
        func (callable): Coroutine to call.
        kwargs : Arguments to pass to the coroutine.

    Returns:
        any: Output of the coroutine.
    """
    async def af():
        async with aiohttp.ClientSession() as cs:
            return await func(cs, **kwargs)
    return asyncio.run(af())


def make_names_str(names : list) -> str:
    """ Convert a list of values into a format compatible for InfluxDB query strings.
        Authors: Shyam Bhuller (University of Oxford)

    Args:
        names (list): List of values.

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


def get_datasources(cs : aiohttp.ClientSession, url : str) -> list[dict]:
    """ Get the urls for each datasource the Grafana dashboards use.
        Authors: Shyam Bhuller (University of Oxford)

    Args:
        cs (aiohttp.ClientSession): Open ClientSession from which to make the http request.
        url (str): Grafana url.

    Returns:
        list[dict]: List of each datasource used.
    """
    data = get_request(cs, url, "api/datasources")
    if data is None:
        raise Exception(f"datasources could not be found by querying {url}")
    return data


def get_queries(panel : dict) -> dict:
    """ Return each query made by the panel.
        Authors: Shyam Bhuller (University of Oxford)

    Args:
        panel (dict): Grafana panel.

    Returns:
        dict: Query along with its name/description.
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
            queries[target["table"]] = target["rawSql"]

    return queries


def search_panel(d : dict | list | str, action : callable, args : dict) -> dict:
    """ Recusrively search for each value in the panel, and perform a function on the value. Panel passed is modified.
        Authors: Shyam Bhuller (University of Oxford)

    Args:
        d (dict | list | str): the panel or an element in the panel.
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
