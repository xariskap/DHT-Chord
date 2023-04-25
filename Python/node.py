from xmlrpc.client import boolean
from main import KS, HS, SLS
import hashlib

def hash_func(data) -> int:
    hash_out = hashlib.sha1()
    hash_out.update(bytes(data.encode("utf-8")))
    return int(hash_out.hexdigest(), 16) % HS

def cw_dist(k1: int, k2: int) -> int:
    """Clockwise distance of 2 keys"""
    
    if k1 <= k2:
        return k2 - k1
    else:
        return (HS) + (k2 - k1)

def comp_cw_dist(k1: int, k2: int, dest: int) -> bool:
    """Returns true if clockwise distance of k1 from dest
    is bigger than clockwise distance of k2 from dest.
    In other words, k2 ∈ (k1, dest]"""

    if cw_dist(k1, dest) > cw_dist(k2, dest):
        return True
    return False

class Node:
    def __init__(self, id: int, pred=None) -> None:
        self.id = id
        # List of dictionaries
        self.items = {}
        # list(table) of lists of the form: [position, node]
        self.f_table = []
        self.pred = pred
        self.succ_list = [None for r in range(SLS)]

    def closest_pre_node(self, key: int) -> 'Node':
        """Returns the last predecessor from THIS node's finger table"""

        current = self
        for i in range(KS):
            # current.successor ∈ (current, key]
            if comp_cw_dist(current.id, current.f_table[i][1].id, key):
                current = current.f_table[i][1]
        return current

    def find_successor(self, key: int) -> 'Node':
        """Returns the node with the shortest
        clockwise distance from the given key"""

        current = self.closest_pre_node(key)
        next = current.closest_pre_node(key)

        while comp_cw_dist(current.id, next.id, key):
            current = next
            next = current.closest_pre_node(key)

        if current.id == key:
            return current

        return current.f_table[0][1]

    def fix_fingers(self) -> None:
        """Called periodically.
        Refreshes finger table entries."""

        for i in range(KS - 1):
            next_in_finger = self.f_table[i + 1]
            next_in_finger[1] = self.f_table[i][1].find_successor(next_in_finger[0])
        #self.print_node()

    def fix_successor_list(self) -> None:
        """Called periodically.
        Refreshes successor list."""

        next_successor = self
        for i in range(SLS):
            if next_successor.f_table[0][1] == self:
                break
            self.succ_list[i] = next_successor.f_table[0][1]
            next_successor = next_successor.f_table[0][1]

    def insert_new_pred(self, new_n: 'Node') -> None:
        """Inserts new node to the network as this node's predecessor.
        Also updates neighboring nodes and necessary finger tables."""
                
        #print("Predecessor node BEFORE node join:")
        #self.pred.print_node(items_print=True)

        # New node's successor is this node
        new_n.f_table.append([(new_n.id + 1) % (HS), self])
        # Predecessor's new successor is the new node
        self.pred.f_table[0][1] = new_n
        # New node's predecessor is this node's predecessor
        new_n.pred = self.pred
        # This node's predecessor is the new node
        self.pred = new_n

        self.move_items_to_pred()
        new_n.initialize_finger_table()
        new_n.fix_successor_list()
        new_n.update_necessary_fingers(joinning=True)
                        
        #print("Predecessor node AFTER node join:")
        #new_n.pred.print_node(items_print=True)

    def insert_item_to_node(self, new_item: tuple, print_item=False) -> None:
        """Insert data in the node."""
        
        if print_item:
            print(f"Item with key {new_item[0]} before updating record:\n{self.items[new_item[0]]}")
        self.items[new_item[0]] = new_item[1]
        if print_item:
            print(f"Item with key {new_item[0]} after updating record:\n{self.items[new_item[0]]}")

    def delete_item_from_node(self, key: str, item_print: bool = False) -> None:
        if key in self.items:
            if item_print:
                print(f"Node before removing item with key {key}:")
                self.print_node(items_print=True)
            del(self.items[key])
            if item_print:
                print(f"Node after removing item with key {key}:")
                self.print_node(items_print=True)
            return
        print(f"Key {key} not found") 

    def move_items_to_pred(self) -> None:    
        """Moves node's items to predecessor.
        Used after a new node joins the network.
        Assumes all predecessors are up to date."""

        for key in sorted(self.items):
            # key ∉ (previous predecessor, new node (current predecessor)]
            if not comp_cw_dist(self.pred.pred.id, hash_func(key), self.pred.id):
                break
            self.pred.items[key] = self.items[key]
            del self.items[key]

    def initialize_finger_table(self) -> None:
        """Initialize node's finger table.
        Assumes node's successor is up to date."""

        i = 1
        while i < KS:
            pos = (self.id + (2**i)) % (HS)

            # While pos ∈ (new_n.id, new_n.successor]
            while (i < KS) and comp_cw_dist(self.id, pos, self.f_table[0][1].id):
                # new_n [i] = new_n.successor
                self.f_table.append([pos, self.f_table[0][1]])
                i += 1
                pos = (self.id + (2**i)) % (HS)

            if i == KS:
                break

            self.f_table.append([pos, self.f_table[0][1].find_successor(pos)])
            i += 1

    def leave(self) -> None:
        """Removes node from the network."""

        # Move all keys to successor node
        self.f_table[0][1].items = self.f_table[0][1].items | self.items
        # Update successor's predecessor
        self.f_table[0][1].pred = self.pred
        # Update predecessor's successor
        self.pred.f_table[0][1] = self.f_table[0][1]

        self.update_necessary_fingers()
    
    def calc_furth_poss_pred(self) -> int:
        """Calculates the furthest possible predecessor id whose 
        last finger table entry position is equal to or higher
        than the current node's ID."""

        if self.id >= 2**(KS-1):
            return self.id - (2**(KS-1))

        return 2**KS + (self.id-(2**(KS-1)))

    def update_necessary_fingers(self, joinning = False) -> None:
        """Updates necessary finger tables on node join/leave"""

        furthest_possible_pred_id = self.calc_furth_poss_pred()
        next_pred = self.pred
        if next_pred == self or next_pred is None:
            return

        i = 0
        # next_pred.id ∈ (furthest_possible_pred_id, self]
        while comp_cw_dist(furthest_possible_pred_id, next_pred.id, self.id):
            next_pred.fix_fingers()
            if i < SLS:
                next_pred.fix_successor_list()
                i += 1
            next_pred = next_pred.pred
            if next_pred == self or next_pred is None:
                return
            
        if not joinning:
            comp = self
        else:
            comp = self.f_table[0][1]

        # next_pred last = current node
        while next_pred.f_table[KS-1][1] == comp:
            next_pred.fix_fingers()
            next_pred = next_pred.pred
            if next_pred == self or next_pred is None:
                return

    def print_node(self, items_print = False, finger_print = False) -> None:
        print(f"Node ID: {hex(self.id)}")
        print(f"Predecessor ID: {hex(self.pred.id)}")
        self.print_succ()
        if items_print:
            print(f"Items in node: {[key for key in self.items.keys()]}")
        if finger_print:
            print("Finger table:")
            for entry in self.f_table:
                print(f"{hex(entry[0])} -> {hex(entry[1].id)}")
        print()

    def print_succ(self):
        true_succ = []
        for succ in self.succ_list:
            if succ is None:
                break
            true_succ.append(hex(succ.id))
        print(f"Successor list: {true_succ}")
    
    def get_first_alive_succ(self) -> 'Node':
        """Returns first successor that hasn't failed"""

        for succ in self.succ_list:
            if succ is not None:
                return succ
        return