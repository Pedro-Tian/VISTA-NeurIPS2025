import os
os.environ['CASTLE_BACKEND'] ='pytorch'
import pandas as pd
import networkx as nx
import numpy as np
import traceback
from sfas import greedy


def check_dag(arr):
    """
    arr np.array
    """
    arr = (arr>0).astype(np.int64)
    G = nx.from_numpy_array(arr, create_using=nx.DiGraph())
    is_dag = nx.is_directed_acyclic_graph(G)
    return is_dag

def find_cycle_min_edge(G):
    try:
        # find any cycle
        cycle = nx.find_cycle(G)
        # print(cycle)
        # find the minimal-weight edge
        min_edge = min(cycle, key=lambda e: G[e[0]][e[1]]['weight'])
        return min_edge
    except nx.NetworkXNoCycle:
        return None

def adjacency_matrix_to_dag(A):
    """
    Greedy method, find cycle in while loop and break it
    """

    G = nx.from_numpy_array(A, create_using=nx.DiGraph())
    
    # remove smallest edge
    iter = 0
    while True:
        min_edge = find_cycle_min_edge(G)
        if min_edge is None:
            break
            
        
        u, v = min_edge
        G.remove_edge(u, v)
        A[u][v] = 0  # update Adj matrix
        iter+=1
        
    return A, iter


def process_scc(G, scc):
    subgraph = G.subgraph(scc)
    node_order = _eades_ordering(subgraph)  # 
    print(node_order)


def improved_adjacency_to_dag(A):
    """
    Based on Strong connected component
    :param A: Adj Matrix
    :return: DAG Adj Matrix
    """
    G = nx.from_numpy_array(A, create_using=nx.DiGraph())
    

    while True:
        scc_list = list(nx.strongly_connected_components(G))
        if len(scc_list) == A.shape[0]:  
            break
        
        
        largest_scc = max(scc_list, key=len)
        if len(largest_scc) == 1:
            continue
            
        
        subgraph = G.subgraph(largest_scc)
        node_order = _eades_ordering(subgraph)  
        
        removed_edges = []
        for u in node_order:
            for v in node_order:
                if subgraph.has_edge(u, v):
                    if node_order.index(u) > node_order.index(v):  # backward edge
                        removed_edges.append((u, v, subgraph[u][v]['weight']))
        
        
        removed_edges.sort(key=lambda x: x)
        for u, v, _ in removed_edges:
            G.remove_edge(u, v)
            A[u][v] = 0
            if nx.is_directed_acyclic_graph(G):
                break
                
    return A

def _eades_ordering(G):
    """
    Eades ordering
    """
    G = nx.DiGraph(G)
    S = []
    sources = [n for n in G.nodes() if G.in_degree(n) == 0]
    sinks = [n for n in G.nodes() if G.out_degree(n) == 0]
    
    while G.nodes():
        print(f"sink: {sinks}")
        print(f"sourcce: {sources}")
        while sinks:
            s = sinks.pop()
            S.append(s)
            G.remove_node(s)
            print("1")
        while sources:
            s = sources.pop()
            S.insert(0, s)
            G.remove_node(s)
            print(2)
        if G.nodes():
            u = max(G.nodes(), key=lambda x: G.out_degree(x) - G.in_degree(x))
            S.append(u)
            G.remove_node(u)
        sources = [n for n in G.nodes() if G.in_degree(n) == 0]
        sinks = [n for n in G.nodes() if G.out_degree(n) == 0]
    return S

def GreedyFAS(A):
    """
    Greedy Feedback Arc Set
    """
    G = nx.from_numpy_array(A, create_using=nx.DiGraph())
    if nx.is_directed_acyclic_graph(G): return A
    
    graph = []
    for edge in G.edges(data=True):
        n1, n2, w = edge
        line = [n1, n2, int(100*w['weight'])]
        graph.append(line)

    eades_order = greedy.compute_order(graph)
    # print(f'eades_order \n{eades_order}')
    
    removed_edges = []
    for u in eades_order:
        for v in eades_order:
            if G.has_edge(u, v):
                if eades_order.index(u) > eades_order.index(v):  # 逆序边
                    removed_edges.append((u, v, G[u][v]['weight']))
    
    
    removed_edges.sort(key=lambda x: x[2])
    for u, v, _ in removed_edges:
        G.remove_edge(u, v)
        A[u][v] = 0
        if nx.is_directed_acyclic_graph(G):
            break

    return A

# test sample
if __name__ == "__main__":
    # directed Adj with cycle
    A = np.array([
        [0, 3, 2, 0],
        [0, 0, 4, 1],
        [0, 0, 0, 5],
        [2, 0, 0, 0]
    ])

    A = np.array([
        [0., 0., 0., 0., 0., 1., 0., 0., 0., 0.],
        [1., 0., 1., 1., 1., 1., 1., 1., 0.66666667, 0.75],
        [0., 0., 0., 1., 0., 0., 0., 0., 0., 0.],
        [0., 0., 0., 0., 0., 1., 0., 0., 0., 0.5],
        [0., 0., 1., 1., 0., 1., 1., 1., 1., 1.],
        [0., 0., 0., 0., 0., 0., 0.33333333, 0., 0., 0.],
        [1., 0., 1., 1., 0., 0.66666667, 0., 1., 0., 0.],
        [1., 0., 1., 1., 0., 1., 0., 0., 0., 0.],
        [1., 0.33333333, 1., 1., 0., 1., 1., 1., 0., 0.],
        [1., 0.25, 1., 0.5,0., 1., 1., 1., 1., 0.]])
    
    print("Original Adj：")
    # print(A)
    print(np.sum(A))
    

    G = nx.from_numpy_array(A, create_using=nx.DiGraph())
    print(f"edges: \n{G.edges(data=True)}")
    graph = []
    for edge in G.edges(data=True):
        n1, n2, w = edge
        line = [n1, n2, int(100*w['weight'])]
        graph.append(line)

    output = greedy.compute_order(graph)
    print(f"output: {output}")

    dag_A = GreedyFAS(A)
    print(check_dag(dag_A), np.sum(dag_A))
    # scc_list = list(nx.strongly_connected_components(G))
    # print("scc_list\n", scc_list)
    # for scc in scc_list:
    #     process_scc(G, scc)
    

    dag_A, iter = adjacency_matrix_to_dag(A.copy())
    
    print("\nTransformed DAG Adj：")
    # print(dag_A)
    print(check_dag(dag_A), iter, np.sum(dag_A))
    print()




