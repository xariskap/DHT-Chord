from xmlrpc.client import boolean
from node import Node, hash_func, cw_dist
import random
import pandas as pd
from main import HS, KS

def parse_csv(filename: str) -> dict:
    """Parses csv and returns a list of items."""

    items = {}
    df = pd.read_csv(filename)

    for i in range(len(df)):
        key = '_'.join([df.values[i][0], str(df.values[i][2])])

        data = {
            'Date': df.values[i][0],
            'Block': df.values[i][1],
            'Plot': df.values[i][2],
            'Experimental_treatment': df.values[i][3],
            'Soil_NH4': df.values[i][4],
            'Soil_NO3': df.values[i][5],
        }
        items[key] = data
    
    return items

class Interface:
    def __init__(self) -> None:
        self.nodes = {}
        
    def build_network(self, node_count: int, node_ids: list = []) -> None:
        """Creates nodes and inserts them into the network."""

        if node_ids == []:
            final_ids = random.sample(range(HS), node_count)
        else: 
            final_ids = node_ids

        for x in final_ids:
            self.node_join(new_node_id=x)
            
    def node_join(self, new_node_id: int, start_node_id: int = None, print_node: boolean = False) -> None:
        """Adds node to the network."""
        
        if new_node_id not in range(HS):
            print(f"{hex(new_node_id)} not in hashing space, can't create node.")
            return
        if print_node:
            print(f"Creating and adding node {hex(new_node_id)} to the network...")
        new_node = Node(new_node_id)
        # First node.
        if not self.nodes:
            new_node.pred = new_node
            # Initialize finger table.
            new_node.f_table = [ [(new_node.id + 2**i) % HS, new_node] for i in range(KS) ]
        else:
            start_node = self.get_node(start_node_id)
            # Find new node successor and insert the new node before it.
            start_node.find_successor(new_node.id).insert_new_pred(new_node)

        self.nodes[new_node.id] = new_node

    def insert_item(self, new_item: tuple, start_node_id: int = None) -> None:
        """Inserts an item (key, value) to the correct node of the network."""

        start_node = self.get_node(start_node_id)
        succ = start_node.find_successor(hash_func(new_item[0]))
        succ.insert_item_to_node(new_item)
        #print(f"Inserting item with hashed key: {hash_func(new_item[0]} to node with ID: {succ.id}")

    def delete_item(self, key: str, start_node_id: int = None, item_print=False):
        """Finds node responsible for key and removes the (key, value) entry from it."""

        start_node = self.get_node(start_node_id)
        start_node.find_successor(hash_func(key)).delete_item_from_node(key,item_print=item_print)
        
    def insert_all_data(self, dict_items: list[tuple], start_node_id: int = None) -> None:
        """Inserts all data from parsed csv into the correct nodes."""

        for dict_item in dict_items:
            self.insert_item(dict_item, start_node_id)
        
    def update_record(self, new_item: tuple, start_node_id: int = None, print_item: bool = False) -> None:
        """Updates the record (value) of an item given its key."""

        start_node = self.get_node(start_node_id)
        responsible_node = start_node.find_successor(hash_func(new_item[0]))
        if new_item[0] in responsible_node.items:
            responsible_node.insert_item_to_node(new_item, print_item=print_item)
            return
        print(f"Could not find item with key {new_item[0]}")
        
    def print_all_nodes(self, items_print = False, finger_print=False) -> None:
        """Prints all nodes of the network"""

        sorted_nodes = sorted(list(self.nodes.items()))
        print([hex(sor_id[0]) for sor_id in sorted_nodes])
        for n in sorted_nodes:
            n[1].print_node(finger_print=finger_print, items_print=items_print)

    def node_leave(self, node_id: int, start_node_id: int = None, print_node = False) -> None:
        """Removes node from network."""

        node_to_remove = self.get_node(start_node_id).find_successor(node_id)
        if node_to_remove.id != node_id:
            print(f"Node {node_id} not found.")
            return
        
        if print_node:
            print("Node that will be removed from network:")
            node_to_remove.print_node(items_print=True)
            print(f"Successor node before {hex(node_id)} leave:")
            successor = node_to_remove.f_table[0][1]
            successor.print_node(items_print=True)
        
        node_to_remove.leave()
        del(self.nodes[node_id])

        if print_node:
            print(f"Successor node after {hex(node_id)} leave:")
            successor.print_node(items_print=True)

    def get_node(self, node_id: int = None) -> Node:
        """Returns node with id node_id. If it's not found,
        it returns the first node that joined the network."""

        # If start_node is specified
        if node_id != None:
            if node_id in self.nodes:
                return self.nodes[node_id]
            else:
                print(f"Node with id {node_id} not found.")
                return
        
        # If nodes dictionary is not empty
        if self.nodes:
            # Return first inserted node
            first_in_node = list(self.nodes.items())[0][1]
            #print(f"Returning first inserted node with id: {hex(first_in_node.id)}")
            return first_in_node

    def range_query(self, start: int, end:int, start_node_id: int = None) -> list[Node]:
        """Lists the nodes in the range [start, end]."""

        nodes_in_range = []
        first_node = self.get_node(start_node_id).find_successor(start)
        current = first_node
        
        # current id ∈ [start, end]
        while cw_dist(start, end) >= cw_dist(current.id, end):
            nodes_in_range.append(current)
            current = current.f_table[0][1]
            if (current == first_node):
                return nodes_in_range

        return nodes_in_range
        
        
    def knn(self, k: int, node_id: int, start_node_id: int = None) -> list[Node]:
        """Lists the k nearest nodes of node, given a specific id."""

        neighbours = []
        
        node = self.exact_match(key=node_id ,start_node_id=start_node_id)
        if node.id is None:
            return

        next_succ  = node.f_table[0][1]
        succ_hops = 0
        next_pred = node.pred
        pred_hops = 0

        while len(neighbours) < k:
            # Difference of next_succ and next_pred distance from node
            succ_pred_difference = (abs(node_id - next_succ.id) % HS) - (abs(node_id - next_pred.id) % HS)
            
            # Next successor is closer
            if succ_pred_difference < 0:
                neighbours.append(next_succ)
                next_succ = next_succ.f_table[0][1]
                succ_hops += 1

            # Next predecessor is closer
            elif succ_pred_difference > 0:
                neighbours.append(next_pred)
                next_pred = next_pred.pred
                pred_hops += 1
            
            # Equal distance
            else:
                if succ_hops <= pred_hops:
                    neighbours.append(next_succ)
                    next_succ = next_succ.f_table[0][1]
                    succ_hops += 1
                else:
                    neighbours.append(next_pred)
                    next_pred = next_pred.pred
                    pred_hops += 1
        
        return neighbours

    def exact_match(self, key: int, start_node_id: int = None) -> Node  | None:
        """Finds and returns node with id same as a given key, if it exists."""

        node = self.get_node(start_node_id).find_successor(key)
        if node.id != key:
            print(f"Couldn't find node with id {key}.")
            return
        return node

    def get_random_node(self) -> Node:
        """Returns random node in the network."""

        random_key = random.sample(sorted(self.nodes), 1)[0]
        return self.nodes[random_key]
    
    def get_id_not_in_net(self) -> int:
        """Returns node id that doesn't already exist in the network."""

        for i in range(HS):
            if i not in self.nodes:
                return i