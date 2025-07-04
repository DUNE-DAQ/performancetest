"""
Created on: 16/04/2025 17:49

Author: Shyam Bhuller

Description: Core functions shared by the auto discovery tools.
"""
import copy
import xml.etree.ElementTree as ET

from collections import ChainMap
from dataclasses import dataclass

import shell, utils

from rich import print, rule

def search_elem_type(elem : ET.ElementTree | ET.Element, type : str) -> callable:
    """ Search for elements by type.

    Args:
        elem (ET.ElementTree | ET.Element): xml element.
        type (str): Value of type to find.

    Returns:
        callable[ET.Element]: Generator of elements.
    """
    return utils.xml_search_elem(elem, "type", type)


def create_cache_map(parent : ET.Element) -> dict:
    """ Create a dictionary of processing units per core and L3 cache domain.

    Args:
        parent (ET.Element): Parent element, either a group or package as defined in lstopo.

    Returns:
        dict: Dictionary of L3 caches, cores and processing units.
    """
    caches = {}
    for cache in utils.xml_search_elem(parent, "type", "L3Cache"): # get the L3 cache domains in the parent element
        c = int(cache.attrib["gp_index"])
        caches[c] = {}
        for core in search_elem_type(cache, "Core"): # cores in each cache
            co = int(core.attrib["os_index"])
            caches[c][co] = [int(pu.attrib["os_index"]) for pu in search_elem_type(core, "PU")] # processing units in each core
    return caches


def create_llc_domain_map(server : str) -> dict:
    """ Parse output of lstopo and create a dictionary of the CPU topology.
        #? Extend to also include PCIe map?
    Args:
        server (str): Server to map.

    Returns:
        dict: CPU map.
    """
    output = shell.run("lstopo -p --of xml", capture = True, host = server).stdout

    tree = ET.ElementTree(ET.fromstring(output))

    socket = {}
    for package in search_elem_type(tree, "Package"): # package = socket
        has_groups = len(list(search_elem_type(package, "Group"))) != 0 # check if the socket has groups, if so there are multiple cache domains and the topology is different (so differnet logic is needed to build the map)


        s = int(package.attrib["os_index"])
        socket[s] = {}
        for numa in search_elem_type(package, "NUMANode"): # get numa regions in each socket
            n = int(numa.attrib["os_index"])
            socket[s][n] = {}

            if not has_groups: # if there are no groups, there is a single cache domain
                socket[s][n] = create_cache_map(package)

        if has_groups:
            for group in search_elem_type(package, "Group"):
                for numa in search_elem_type(group, "NUMANode"):
                    n = int(numa.attrib["os_index"])

                socket[s][n] = create_cache_map(group)

    return socket

@dataclass
class Element:
    """ Representation of a single object in the core map.
    """
    id : int
    children : list[int] # only keep the ID not the object itself
    parent : "Element"
    type : str = None

    def __repr__(self):
        return f"{self.type}(id : {self.id}, children : {len(self.children) if self.children else None}, parent : {self.parent})"


    def get_type(self, type : str) -> list:
        """ Search and return child objects by their type.

        Args:
            type (str): type of element to find.

        Returns:
            list: list of elements of that type.
        """
        cores = []
        if self.children:
            for c in self.children:
                if c.type == type:
                    cores.append(c)
                else:
                    cores.extend(c.get_type(type))
        return cores


class ElementList:
    """ A list of elements with special properties, including when items are called, they are removed from the list and domain map.
    """
    def __init__(self, elements : list, domain_map):
        self.elements = elements
        self.map = domain_map
        return


    def __getitem__(self, i : int):
        e = self.elements[i]
        self.elements.remove(e)
        if self.map: self.map.remove(e)
        return e


    def get_id(self, i : int) -> Element:
        """ Get the Element that matches the specific id.

        Args:
            i (int): id.

        Returns:
            Element: Found Element, only returns the first occurance found.
        """
        for e in self.elements:
            if e.id == i:
                self.elements.remove(e)
                self.map.remove(e)
                return e
        raise Exception(f"Element with id {i} was not found!")

    @property
    def first(self) -> Element:
        """ Get the first Element in the list.

        Returns:
            Element: First element.
        """
        return self.__getitem__(0)


    def __len__(self):
        return len(self.elements)


class CoreMap:
    """ Map of CPU processing units. Converts a parsed output of lstopo into a Elements for each type of resouce in the lstopo map (Core, PU, NUMA, Socket etc.).
        Each Element is assigned parents and children, so the nested data is represented as a flat list to better allow getting an Element from each reosuce layer.
    """
    def __init__(self, domain_map : dict):
        self.elements = []
        CoreMap.ParseMap(domain_map, element_list = self.elements)

        unique_types = []
        for e in self.elements:
            if e.type not in unique_types:
                unique_types.append(e.type)
        for t in unique_types:
            self.__make_func__(t)

        self.__offset_core_id__()

        return

    def __make_func__(self, type : str):
        """ Create a property function for a given element type in the coremap.
            This property function returns the appropriate ElementList for that given type.

        Args:
            type (str): The type to make function for.
        """
        def func(self) -> ElementList:
            return ElementList([i for i in self.elements if i.type == type], self)
        setattr(CoreMap, type.lower(), property(func))


    def __offset_core_id__(self):
        """ Offset the Core IDs from the lstopo map as they are the same for each socket.
        """
        offset = len(self.core) // len(self.socket)
        for c in self.core.elements:
            c.id = c.id + c.parent.parent.parent.id * offset
        return


    def remove(self, e : Element, remove_from_parent : bool = True):
        """ Removes an Element from the CoreMap. To correctly do so, it does the following for the Element to be removed:
            #* remove any reference to another element: find its parent, and remove self from children
            #* remove any reference to another element: find its children, and remove self from parent
            #* remove from self.elements
        Args:
            e (Element): Element to remove
            remove_from_parent (bool, optional): Optinally remove from the parent. Required logic for a recusive implementation. Defaults to True.
        """
        if e is not None:
            if e.children:
                for c in e.children:
                    self.remove(c, False)

            if e in self.elements:
                self.elements.remove(e)

            if e.parent is not None:
                if remove_from_parent:
                    if e in e.parent.children:
                        e.parent.children.remove(e)
                if (len(e.parent.children) == 0): self.remove(e.parent)
            else:
                self.remove(e.parent)
        return


    def print(self):
        """Pretty print representation of the CoreMap
        """
        top_elements = [e for e in self.elements if e.parent is None]
        out = self.__remake_domain_map(top_elements)
        print(out)
        return


    def __remake_domain_map(self, elements : list[Element]) -> list:
        """ Nested list representation of the CoreMap for visulization. Keys and values are represented as strings.

        Args:
            elements (list[Element]): List of elements.

        Returns:
            list: list 
        """
        out = []
        for e in elements:
            k = f"{e.type}:{e.id}"
            if e.children:
                v = self.__remake_domain_map(e.children)
                out.append({k: v})
            else:
                out.append(k)
        return out


    @staticmethod
    def ParseMap(container, parent : Element = None, element_list : list = []):
        """ Parse the lstopo output, and create Elements from each resource recursively.

        Args:
            container: a list or dictionary from the lstopo output that represents a resource.
            parent (Element, optional): Parent element (if exists or the resource has a parent). Defaults to None.
            element_list (list, optional): _description_. Defaults to [].
        """
        if type(container) == dict:
            for item in container.items():
                if hasattr(item[1], "__iter__"):
                    e = Element(item[0], [], parent)
                    if parent: parent.children.append(e)
                    element_list.append(e)
                    CoreMap.ParseMap(item[1], e, element_list)
                    CoreMap.AssignElementType(e)

                    #* loop through all items, and return list of elements who are children of this item
                    #* assign the parent to each child
                    #* add elements to a flat list

        else: # assume list-like
            for item in container:
                if hasattr(item, "__iter__"):
                    e = Element(None, [], parent)
                    if parent: parent.children.append(e)
                    element_list.append(e)
                    CoreMap.ParseMap(item)
                    CoreMap.AssignElementType(e)
                else:
                    e = Element(item, None, parent, "PU") # this is the deepest part of the map
                    parent.children.append(e) # add child to parent
                    element_list.append(e) # add element to flat list
                    CoreMap.AssignElementType(e)
        return

    @staticmethod
    def AssignElementType(e : Element):
        """ Assigns the Elements type based on the parents/child type. The current hierarchy of reasources is (top to bottom):
            Socket -> NUMA -> Cache -> Core -> PU.

        Args:
            e (Element): Element
        """
        # code asssumes all children are the same type (which should be true)
        if not e.parent:
            e.type = "Socket" # we are at the highest level
        elif not e.children:
            e.type == "PU" # we are at the lowest level
        elif e.children[0].type == "PU":
            e.type = "Core"
        elif e.children[0].type == "Core":
            e.type = "Cache"
        elif e.children[0].type == "Cache":
            e.type = "NUMA"
        elif e.children[0].type == None:
            pass
        else:
            raise Exception(f"do not know how to interpret Element with type: {e.type}")
        return

def core_list_to_str(cores : list[int]) -> str:
    """ Convert a list of cores to a string format for the json file.

    Args:
        cores (list[int]): List of cores.

    Returns:
        str: Core list string.
    """
    #! for now, just use join, but can try to condense it later on.
    return ",".join(str(c) for c in cores)


def assign_cores(core_map : CoreMap, cores : list[Element], max_cores : int) -> list[int]:
    """ Assign processing units to a thread. Used for cache aware pinning.

    Args:
        core_map (CoreMap): CPU map of server.
        cores (list[Element]): List of cores to assign processing units from.
        max_cores (int): Maximum number of procssing units to assign to a thread.

    Returns:
        list[int]: assigned processing units
    """
    pus = []
    while len(pus) < max_cores:
        if len(cores) == 0:
            raise Exception("Ran out of cores to assign!")
        next_core = ElementList(cores, core_map).first
        pus.extend([c.id for c in next_core.children])
    return pus


def fill_pinning_map_cache(pinning : dict, cpu_alloc : ChainMap, core_map : CoreMap) -> dict:
    """ Assign processing units to threads. Is L3 cache aware. Thread names are prioritized by order in the dictionary.

    Args:
        pinning (dict): Pinning dictionary.
        cpu_alloc (ChainMap): cpu reosurce allocation map.
        core_map (CoreMap): CPU map of server.

    Returns:
        dict: Filled pinning map.
    """
    # calculate the number of allowed pus per cache
    pus_per_cache = len(core_map.cache.elements[-1].children) * len(core_map.core.elements[-1].children) # true for cache that does not have the first core in each numa, then subtract 1.

    # First exclude the first core (first two processing units) in each numa region
    for n in core_map.numa.elements:
        core_map.core.get_id(min([c.id for c in n.get_type("Core")]))

    pinning_dict = {k : {"threads" : {}} for k in pinning}
    for app in pinning:
        n_rte = len([k for k in pinning[app]["threads"] if "rte" in k]) # count the number of rte workers for this daq application

        for numa_region in core_map.numa.elements: # get the numa region, but do not remove it from the map yet
            if numa_region.id == pinning[app]["numa"]: break

        # count the total number of cores requested to be assigned to this application, and check it is sensible
        total_requested_cores = n_rte * cpu_alloc["rte"] + sum([v for k, v in cpu_alloc.items() if k != "rte"])
        print(f"{total_requested_cores=}")

        cores_available = len(numa_region.get_type("PU"))
        if total_requested_cores > cores_available:
            raise Exception(f"number of cores required {total_requested_cores} exceeds the number available {cores_available}")

        # calculate the number of caches to assign for each thread group, and check this can also be fulfilled. 
        requested_caches = 0
        requested_caches_map = []
        for i in cpu_alloc.maps:
            n = 0
            for k, v in i.items():
                if k == "rte":
                    n += n_rte
                else:
                    n += v
            requested_caches_map.append(int(n / pus_per_cache) + (n % pus_per_cache > 0))
            requested_caches += int(n / pus_per_cache) + (n % pus_per_cache > 0)
        print(f"{requested_caches=}")

        caches = numa_region.get_type("Cache")
        if requested_caches > len(caches):
            raise Exception(f"number of cache domains required ({requested_caches}) exceeded the number available ({len(caches)})")

        # Now find the cache corresponding to the rte workers, and assign the rte worker threads
        rte_cache = None
        for t in pinning[app]["threads"]:
            if "rte-worker" in t:
                pu = int(t.split("-")[-1])
                for c in caches:
                    if pu in [i.id for i in c.get_type("PU")]:
                        if rte_cache is None:
                            rte_cache = c
                        # else:
                            # if rte_cache.id != c.id:
                            #     raise Exception("rte workers should be assigned from the same L3 cache domain!")
                # before assigning the other cores, assign rtes first as these are provided by the configuration
                pinning_dict[app]["threads"][t] = str(pu)
                core_map.pu.get_id(pu)
        caches.remove(rte_cache)

        # collect the cores for each cache needed in each thread group
        groups = []
        for n, m in zip(requested_caches_map, cpu_alloc.maps):
            g = []
            if "rte" in m:
                g = [*rte_cache.children] # need to make a new list otherwise the core map will be incorrectly updated.
                for i in range(n-1):
                    g.extend(caches.pop(0).children)
                groups.append(g)
            else:
                for i in range(n):
                    g.extend(caches.pop(0).children)
                groups.append(g)

        # assign the remaining cores
        ccps = None
        for t in pinning[app]["threads"]:
            if "rte-worker" in t: # this assignment happens before, as lcores are defined by the configuration
                continue

            # infer the thread type
            if ("cleanup" in t) or ("consumer" in t) or ("periodic" in t):
                prefix = "ccp"
            else:
                prefix = t.split("-")[0]

            # find the core group this thread type is within
            cg = [g for g, m in zip(groups, cpu_alloc.maps) if prefix in m]
            if len(cg) > 1:
                raise Exception("cannot have the same thread type in different cache groups.")
            elif len(cg) == 0:
                raise Exception(f"do not know how to assign cores to thread {t}")
            cg = cg[0]

            if prefix == "ccp": # cleanup, consumer and periodic threads are unique because they are all assigned the same cores
                if ccps is None:
                    ccps = assign_cores(core_map, cg, cpu_alloc["ccp"])
                pinning_dict[app]["threads"][t] = core_list_to_str(ccps)
            else:
                pus = assign_cores(core_map, cg, cpu_alloc[prefix])
                pinning_dict[app]["threads"][t] = core_list_to_str(pus)

        pinning_dict[app]["parent"] = core_list_to_str(ccps)
    return {"daq_application" : pinning_dict}


def validate_cpu_resource_map(cpu_map : CoreMap, resource_alloc : list[dict]):
    """ Check some properties of the resource allocation and print some information if resource allocation is not optimal.

    Args:
        cpu_map (CoreMap): Map of CPU resources.
        resource_alloc (list[dict]): Provided resource allocation.
    """
    has_multiple_caches = len(cpu_map.numa.elements[0].children) > 1

    if not has_multiple_caches and len(resource_alloc.maps) > 1:
        print("hardware does not have multiple cache boundaries, cache regions will be merged into one")
    if has_multiple_caches and len(resource_alloc.maps) == 1:
        print('Warning: CPU has multiple cache boundaries, but only one cache region was requested. Consider using the default resource allocation (remove "resource_allocation" from the template), or define multiple cache regions')

    return


def create_cpu_pinning(threads : dict, cpu_map : CoreMap, resource_alloc : ChainMap) -> tuple[dict, dict]:
    """ Assign processing units to threads for provided daq applications.

    Args:
        threads (dict): Threads for each daq application.
        cpu_map (CoreMap): Map of CPU resources from the given host machine.
        resource_alloc (ChainMap): Provided resource allocation.

    Returns:
        tuple[dict, dict]: pinning that is use while running and while configuring.
    """
    print(rule.Rule("CPU map"))
    cpu_map.print()

    pus_numa = [[p.id for p in n.get_type("PU")] for n in cpu_map.numa.elements]

    # pinnig while running
    pinning = fill_pinning_map_cache(threads, resource_alloc, cpu_map)
    print(rule.Rule("CPU pinning running"))
    print(pinning)

    # pinning during conf
    pinning_conf = copy.deepcopy(pinning)
    for app in pinning_conf["daq_application"]:
        if not app[-2:].isalpha():
            numa = int(app[-1])
        else:
            numa = int(app[-2])
        pinning_conf["daq_application"][app]["parent"] = core_list_to_str(pus_numa[numa])
    print(rule.Rule("CPU pinning all"))
    print(pinning_conf)

    print(rule.Rule("remaining CPUs in CPU map"))
    cpu_map.print()
    return pinning, pinning_conf
