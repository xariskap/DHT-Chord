import interface as iff
from time import perf_counter
import random
from main import KS
import matplotlib.pyplot as plt

HS = 2**KS

def benchmark(NC: int, results: dict) -> dict:
    interface = iff.Interface()

    # Build network with NC nodes
    build_start = perf_counter()
    interface.build_network(NC)
    build_end = perf_counter()

    # Insert all data to the network
    data_start = perf_counter()
    items = iff.parse_csv("NH4_NO3.csv")
    interface.insert_all_data(items.items())
    data_end = perf_counter()

    # Generate random numbers to use for benchmarking
    run_count = 10
    random_nodes = random.sample(sorted(interface.nodes), run_count*2)
    (leave_n, ex_match_n) = (random_nodes[:run_count], random_nodes[run_count:])

    search_keys = random.sample(range(HS), run_count)
    first_node = interface.get_node()

    join_nodes = []
    count = 0
    for i in range(HS):
        if i not in interface.nodes:
            count += 1
            join_nodes.append(i)
            if count >= run_count//2:
                break

    in_keys = []
    in_data = []
    up_data = []

    for i in range(run_count):
        in_keys.append(f"In key {i}")
        in_data.append(f"In data {i}")
        up_data.append(f"Updata {i}")

    # Start process benchmarking NC Nodes

    # Insert key
    print("Benchmarking insert key...")
    in_key_start = perf_counter()
    for index, key in enumerate(in_keys):
        interface.insert_item((key, in_data[index]), first_node.id)
    in_key_end = perf_counter()

    # Update record based on key
    print("Benchmarking Update record based on key...")
    up_key_start = perf_counter()
    for key in in_keys:
        interface.update_record((key, up_data[index]), first_node.id)
    up_key_end = perf_counter()

    # Delete key
    print("Benchmarking Delete key...")
    del_key_start = perf_counter()
    for key in in_keys:
        interface.delete_item(key=key, start_node_id=first_node.id)
    del_key_end = perf_counter()

    # Key lookup 
    print("Benchmarking Key lookup...")
    query_start = perf_counter()
    for key in search_keys:
        first_node.find_successor(key)
    query_end = perf_counter()

    # Node join
    print("Benchmarking Node join...")
    join_start = perf_counter()
    for key in join_nodes:
        interface.node_join(new_node_id=key)
    join_end = perf_counter()

    # Exact match
    print("Benchmarking Exact match...")
    ex_match_start = perf_counter()
    for key in ex_match_n:
        interface.exact_match(key=key)
    ex_match_end = perf_counter()

    # Node Leave
    print("Benchmarking Node Leave...")
    leave_start = perf_counter()
    for key in leave_n:
        interface.node_leave(key)
    leave_end = perf_counter()

    # Range query
    print("Benchmarking Range query...")
    range_start = perf_counter()
    for key in search_keys:
        interface.range_query(key, (key+20) % HS )
    range_end = perf_counter()

    # kNN query
    print("Benchmarking kNN query...")
    knn_start = perf_counter()
    for key in join_nodes:
        interface.knn(5, key)
    knn_end = perf_counter()

    #results['Build'][NC] = (build_end - build_start) * 1000
    #results['Insert all data'][NC] = (data_end - data_start) * 1000
    results['Insert key'][NC] = (in_key_end - in_key_start) * 1000 / run_count
    results['Delete key'][NC] = (del_key_end - del_key_start) * 1000 / run_count
    results['Update key'][NC] = (up_key_end - up_key_start) * 1000 / run_count
    results['Key lookup'][NC] = (query_end - query_start) * 1000 / run_count
    results['Node Join'][NC] = (join_end - join_start) * 1000 / (run_count/2)
    results['Node Leave'][NC] = (leave_end - leave_start) * 1000 / run_count
    #results['Massive Nodes\' failure'][NC] = (mnn_end - mnn_start)
    results['Exact match'][NC] = (ex_match_end - ex_match_start) * 1000 / run_count
    results['Range Query'][NC] = (range_end - range_start) * 1000 / run_count
    results['kNN Query'][NC] = (knn_end - knn_start) * 1000 / run_count
    return results

def benchmark_all() -> dict:
    answer = {
        #"Build": {},
        #"Insert all data": {},
        "Insert key": {},
        "Delete key": {},
        "Update key": {},
        "Key lookup": {},
        "Node Join": {},
        "Node Leave": {},
        #"Massive Nodes' failure": {},
        "Exact match": {},
        "Range Query": {},
        "kNN Query": {}
    }
    for i in range(20, 301, 40):
        print(f"\nBenchmarking {i} nodes...\n")
        answer = benchmark(i, answer)
    return answer

def results_print(results: dict) -> None:
    for process in results.items():
        print(f"\n{process[0]} times:")
        for node_count, time in process[1].items():
            print(f"{process[0]} time for {node_count} nodes: {time}")

def plot_results(results: dict) -> dict[plt.plot]:
    # X axis = Node count, Y axis = Time
    plots = {}
    for process in results.items():
        plt.figure(process[0])
        plots[process[0]] = plt.plot([nc[0] for nc in process[1].items()],\
            [t[1] for t in process[1].items()])
        if process[0] != "Node Join" and process[0] != "Node Leave":
            plt.axis([20, 300, 0, 0.1])
        plt.xlabel("Node Count")
        plt.ylabel("Time (ms)")
        plt.title(process[0])
        plt.show()

    return plots

results = benchmark_all()
plot_results(results)
#results_print(benchmark_all())