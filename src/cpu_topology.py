"""
Created on: 22/04/2026 13:24

Author: Shyam Bhuller

Description: Code used to extract and parse CPU topology information for a computer.
"""

import xml.etree.ElementTree as ET

import shell, utils
from dataclasses import dataclass

def search_elem_type(elem : ET.ElementTree | ET.Element, type : str) -> callable:
    """ Search for elements by type.

    Args:
        elem (ET.ElementTree | ET.Element): xml element.
        type (str): Value of type to find.

    Returns:
        callable[ET.Element]: Generator of elements.
    """
    return utils.xml_search_elem(elem, "type", type)


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


def get_ls_topo_output(server : str) -> ET.ElementTree:
    """ Get the output of lstopo in xml form.

    Args:
        server (str): Server to run command on.

    Returns:
        ET.ElementTree: output as an xml ElementTree.
    """
    output = shell.run("lstopo -p --of xml", capture = True, host = server).stdout

    tree = ET.ElementTree(ET.fromstring(output))
    return tree


def create_llc_domain_map(topo : ET.ElementTree) -> dict:
    """ Convert the xml lstopo output into a pythonic object.

    Args:
        topo (ET.ElementTree): xml lstopo output.

    Returns:
        dict: pythonic map of CPU topology.
    """
    socket = {}
    for package in search_elem_type(topo, "Package"): # package = socket
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


def get_isolated_cores(host : str) -> list[int]:
    """ Get CPU cores isolated from kernel processes.

    Args:
        host (str): host machine name.

    Returns:
        list[int]: list of isolated processing units.
    """
    rte_cpus = []
    try:
        out = shell.run("cat /sys/devices/system/cpu/isolated", capture = True, host = host).stdout
        for i in out.decode().split(","):
            int_list = [int(j) for j in i.split("-")]
            rte_cpus.extend(list(range(min(int_list), max(int_list)+1)))
    except ValueError:
        print("cannot automatically detect isolated CPUS")
    return rte_cpus


def get_and_create_llc_domain_map(server : str) -> dict:
    """ Parse output of lstopo and create a dictionary of the CPU topology.
        #? Extend to also include PCIe map?
    Args:
        server (str): Server to map.

    Returns:
        dict: CPU map.
    """
    return create_llc_domain_map(get_ls_topo_output(server))
