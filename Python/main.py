import interface as iff
import random

# Key size (bits)
KS = 4
# Hashing space
HS = 2**KS
# Successor list size
SLS = 3
# Node count
NC = 5

def main():
    # Nodes creation
    interface = iff.Interface()
    
    # Create random network with NC nodes
    interface.build_network(NC)

    # Create predefined network with node ids
    #node_ids=[6, 5, 9, 10, 3, 14]
    #interface.build_network(node_count=len(node_ids), node_ids=node_ids)

    # Data insertion
    items = iff.parse_csv("NH4_NO3.csv")
    interface.insert_all_data(items.items())
    interface.print_all_nodes(finger_print=True, items_print=False)
    input("Press any key to continue...\n")

    # Update record based on key
    random_key = random.sample(sorted(items), 1)[0]
    data = "This is a test string to demonstrate the update record function."
    interface.update_record((random_key, data), start_node_id=None, print_item=True)
    input("Press any key to continue...\n")

    # Delete key
    interface.delete_item(random_key, item_print=True)
    input("Press any key to continue...\n")

    # Key lookup
    lookup = {"key": 12, "start_node_id": None}
    print(f"Looking up responsible node for key {hex(lookup['key'])} starting from node {lookup['start_node_id']}:")
    interface.get_node(lookup["start_node_id"])\
        .find_successor(lookup["key"]).print_node(items_print=False, finger_print=True)
    input("Press any key to continue...\n")

    # Exact match
    rnid = interface.get_random_node().id
    exact_match = {"key":rnid, "start_node_id": None}
    print(f"Searching node with id {exact_match['key']} starting from node {exact_match['start_node_id']}:")
    interface.exact_match(exact_match["key"], exact_match["start_node_id"]).\
        print_node(items_print=True, finger_print=True)

    # Node Join
    rnid = interface.get_id_not_in_net()
    interface.node_join(rnid, print_node=True)
    interface.print_all_nodes()
    input("Press any key to continue...\n")

    # Node Leave
    rnid = interface.get_random_node().id
    interface.node_leave(rnid, print_node=True)
    interface.print_all_nodes()
    input("Press any key to continue...\n")
    
    # Range query
    rq = {"start": 5, "end": 10}
    print(f"Nodes in range: [{hex(rq['start'])}, {hex(rq['end'])}]:")
    print([hex(n.id) for n in interface.range_query(rq["start"], rq["end"])])
    input("Press any key to continue...\n")

    # kNN query
    rnid = interface.get_random_node().id
    kNN = {"k": 3,"key": rnid}
    print(f"{kNN['k']} nearest neighbours of {hex(kNN['key'])}:")
    print([hex(n.id) for n in interface.knn(kNN["k"], kNN["key"])])
    input("Press any key to continue...\n")
    
if __name__ == "__main__":
    main()