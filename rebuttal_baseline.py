import os
os.environ['CASTLE_BACKEND'] ='pytorch'
import pandas as pd
import networkx as nx
import numpy as np
import traceback
from cdt.metrics import SID
import castle
from castle.common import GraphDAG

from castle.datasets import DAG, IIDSimulation
from castle.algorithms import CORL, Notears, GOLEM, GraNDAG, DAG_GNN
from dodiscover.toporder import SCORE, DAS, NoGAM, CAM, SCORE_MOD

from dodiscover.context_builder import make_context

from dcilp.dcdilp_Ph1MB1 import *
from dcilp.dcdilp_Ph1MB1 import _threshold_hard, _MBs_fromInvCov
import dcilp.utils_files.utils as utils
from dcilp.utils_files.gen_settings import gen_data_sem_original

from mas_approximation import MAS_Approx
from merge import adjacency_matrix_to_dag, GreedyFAS

import argparse
import logging


import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'causal-discovery')))


def set_logger(args):
    log_path = f"./experiment_logs/NeurIPSRebuttal_N{args.nodes}{args.type}{args.h}_{args.sem_type}_norm{args.normalized}_baseline_{args.model}.log"
    if os.path.exists(log_path): os.remove(log_path)
    
    # logger = logging.getLogger(__name__)
    logger = logging.getLogger('app')
    log_level = logging.DEBUG
    logger.setLevel(log_level)

    log_formatter = logging.Formatter('[%(asctime)s][%(name)s][%(levelname)s] %(message)s')
    file_handler = logging.FileHandler(log_path)
    file_handler.setLevel(log_level)
    file_handler.setFormatter(log_formatter)
    logger.addHandler(file_handler)

    # log_formatter = logging.Formatter('%(message)s')
    # console_handler = logging.StreamHandler()
    # console_handler.setLevel(log_level)
    # console_handler.setFormatter(log_formatter)
    # logger.addHandler(console_handler)
    
    return logger
    
    

def get_MB(data, ice_lam_min = 0.1, ice_lam_max = 0.3, ice_lam_n = 10):

    data = data - np.mean(data, axis=0, keepdims=True)
    # Method ICE empirical

    t0 = timer()
    out = ice_sparse_empirical(data, lams=np.linspace(ice_lam_min, \
                                                    ice_lam_max, \
                                                    ice_lam_n))
    Theta = _threshold_hard(out[0], tol=1e-3)

    MBs = _MBs_fromInvCov(Theta)
    t1 = timer()
    print(t1-t0)
    print(MBs)
    return MBs


def split_graph(markov_blankets, true_dag, X):

    sub_X_list = []
    sub_true_dag_list = []
    sub_nodes_list = []
    n_nodes = len(markov_blankets)

    for i in range(n_nodes):
        blanket_indices = np.where(markov_blankets[i])[0]
        # print(i, blanket_indices)
        if len(blanket_indices) <= 1:
            continue
        # 把节点 i 自己也加进去
        nodes = set(blanket_indices)
        nodes.add(i)
        nodes = sorted(nodes)

        sub_X = X[:, nodes]

        sub_dag = true_dag[np.ix_(nodes, nodes)]

        sub_X_list.append(sub_X)
        sub_true_dag_list.append(sub_dag)
        sub_nodes_list.append(nodes)

    return sub_X_list, sub_true_dag_list, sub_nodes_list     

def merge_graph_voting(sub_nodes_list, sub_causal_matrix_list, true_dag):
    """
    A naiive voting merge method, directly weighted sum all edges mentioned in `sub_causal_matrix_list`

    sub_nodes_list: 2-D List
    sub_causal_matrix_list: List of np arrays
    """
    recover_graph = np.zeros(true_dag.shape)
    count = np.zeros(true_dag.shape)


    for nodes, sub_causal_matrix in zip(sub_nodes_list, sub_causal_matrix_list):
        recover_graph[np.ix_(nodes, nodes)] += sub_causal_matrix
        count[np.ix_(nodes, nodes)] += 1
    
    count = np.maximum(count, np.ones(true_dag.shape))
    recover_graph = recover_graph/count
    
    return recover_graph

def check_dag(arr):
    """
    arr np.array
    """
    G = nx.from_numpy_array(arr, create_using=nx.DiGraph())
    is_dag = nx.is_directed_acyclic_graph(G)
    return is_dag

def eval_met(est_dag, true_dag):
    met = castle.metrics.MetricsDAG(est_dag, true_dag)
    sid = SID(est_dag, true_dag).max()
    met.metrics['sid'] = sid 
    return met



def infer_causal(args, X, true_dag):
    causal_matrix_order, causal_matrix, met2 = None, None, None
    if args.model == 'CORL':
        # rl learn
        model = CORL(encoder_name='transformer',
                decoder_name='lstm',
                reward_mode='episodic',
                reward_regression_type='GPR',
                batch_size=64,
                input_dim=64,
                embed_dim=64,
                iteration=1000,
                device_type='gpu',
                device_ids=2)
        model.learn(X)
        causal_matrix = model.causal_matrix
    elif args.model == 'NOTEARS':
        model = Notears()
        model.learn(X)
        causal_matrix = model.causal_matrix
    elif args.model == 'GOLEM':
        model = GOLEM(num_iter=1e4)
        model.learn(X)
        causal_matrix = model.causal_matrix
    elif args.model == 'DAGGNN':
        model = DAG_GNN()
        model.learn(X)
        causal_matrix = model.causal_matrix
    elif args.model == 'GRANDAG':
        model = GraNDAG(input_dim=X.shape[1], iterations = 100000)
        model.learn(X)
        causal_matrix = model.causal_matrix
    elif args.model == 'SCORE':
        context = make_context().variables(data = pd.DataFrame(X)).build()
        model = SCORE() 
        # print("before learning")
        model.learn_graph(pd.DataFrame(X), context)
        # print("Finish learning")
        causal_matrix_order = nx.adjacency_matrix(model.order_graph_, range(args.nodes)).todense()
        # print(causal_matrix_order, true_dag)
        # logger.info(f"nodes info: {model.order_graph_.nodes()}")
        try:
            # met2 = castle.metrics.MetricsDAG(model.order_graph_, nx.from_numpy_array(true_dag))
            met2 = eval_met(causal_matrix_order, true_dag)
            # met2 = castle.metrics.MetricsDAG(causal_matrix_order, true_dag)
        except Exception as e:
            met2=None
            logger.info(f"[Error] met2=None: {traceback.format_exc()}")
        # res2.append(met2.metrics)
        causal_matrix = nx.adjacency_matrix(model.graph_, range(args.nodes)).todense()
    elif args.model == 'SCORE_MOD':
        context = make_context().variables(data = pd.DataFrame(X)).build()
        model = SCORE_MOD(pre_prune = args.preprune) 
        # print("before learning")
        model.learn_graph(pd.DataFrame(X), context)
        # print("Finish learning")
        causal_matrix_order = nx.adjacency_matrix(model.order_graph_, range(args.nodes)).todense()
        print(causal_matrix_order, true_dag)
        try:
            met2 = eval_met(causal_matrix_order, true_dag)
        except Exception as e:
            met2=None
            logger.info(f"[Error] met2=None: {traceback.format_exc()}")
        # res2.append(met2.metrics)
        causal_matrix = nx.adjacency_matrix(model.graph_, range(args.nodes)).todense()
    elif args.model == 'DAS':
        context = make_context().variables(data = pd.DataFrame(X)).build()
        model = DAS() 
        model.learn_graph(pd.DataFrame(X), context)
        causal_matrix_order = nx.adjacency_matrix(model.order_graph_, range(args.nodes)).todense()
        met2 = eval_met(causal_matrix_order, true_dag)
        # res2.append(met2.metrics)
        causal_matrix = nx.adjacency_matrix(model.graph_, range(args.nodes)).todense()
    elif args.model == 'CAM':
        context = make_context().variables(data = pd.DataFrame(X)).build()
        model = CAM() 
        model.learn_graph(pd.DataFrame(X), context)
        causal_matrix_order = nx.adjacency_matrix(model.order_graph_, range(args.nodes)).todense()
        met2 = eval_met(causal_matrix_order, true_dag)
        # res2.append(met2.metrics)
        causal_matrix = nx.adjacency_matrix(model.graph_, range(args.nodes)).todense()
    elif args.model == 'NoGAM':
        context = make_context().variables(data = pd.DataFrame(X)).build()
        model = NoGAM() 
        model.learn_graph(pd.DataFrame(X), context)
        causal_matrix_order = nx.adjacency_matrix(model.order_graph_, range(args.nodes)).todense()
        met2 = eval_met(causal_matrix_order, true_dag)
        # res2.append(met2.metrics)
        causal_matrix = nx.adjacency_matrix(model.graph_, range(args.nodes)).todense()

    return causal_matrix_order, causal_matrix, met2

def column_normalize(matrix):
    norms = np.sqrt(np.sum(matrix**2, axis=0) + 1)
    return matrix / norms

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='causal inference')

    parser.add_argument('--model', default='SCORE', type=str, 
                        help='model name')
    parser.add_argument('--nodes', default=10, type=int,
                        help="number of nodes")
    parser.add_argument('--h', default=2, type=int,
                        help="number of edges")
    parser.add_argument('--type', default='ER', type=str,
                        help="type of graph")
    parser.add_argument('--method', default='linear', type=str,
                        help="?")
    parser.add_argument('--sem_type', default='gauss', type=str,
                        help="?")
    parser.add_argument('--repeat', default=1, type=int,
                        help="number of repeated iterations")
    parser.add_argument('--num_observation', default=2000, type=int,
                        help="number of observation data")
    parser.add_argument('--preprune', type=bool,
                        help="Pre-prunning strategy")
    parser.add_argument('--normalized', default=False, type=bool,
                        help="normalized")

    args = parser.parse_args()

    # setup log
    logger = set_logger(args)
    # logger.setLevel(logging.DEBUG)

    # type = 'ER'  # or `SF`
    # h = 5  # ER2 when h=5 --> ER5
    # n_nodes = 50
    n_edges = args.h * args.nodes
    # method = 'linear'
    # sem_type = 'gauss'

    res = []
    res2 = []



    print(args.type, args.h, args.nodes, args.model)

    for _ in range(args.repeat):
        logger.info(f"=========== repeat {_+1} ===========")
        if args.type == 'ER':
            weighted_random_dag = DAG.erdos_renyi(n_nodes=args.nodes, n_edges=n_edges,
                                                weight_range=(0.5, 2.0), seed=1000+_*100)
        elif args.type == 'SF':
            weighted_random_dag = DAG.scale_free(n_nodes=args.nodes, n_edges=n_edges,
                                                weight_range=(0.5, 2.0), seed=1000+_*100)
        else:
            raise ValueError('Just supported `ER` or `SF`.')
        # logger.info(f"weighted_random_dag before normal: {weighted_random_dag}\n")
        if args.normalized:
            weighted_random_dag = column_normalize(weighted_random_dag)
        # logger.info(f"weighted_random_dag: {weighted_random_dag}\n")

        dataset = IIDSimulation(W=weighted_random_dag, n=args.num_observation,
                                method=args.method, sem_type=args.sem_type)
        true_dag, X = dataset.B, dataset.X
        logger.info(f"X: {X.shape}\n{X}")
        logger.info(f'true_dag\n{true_dag}')


        # compute the causal matrix directly
        causal_matrix_order, causal_matrix, met2 = infer_causal(args, X, true_dag)
        if met2: res2.append(met2.metrics)

        # plot est_dag and true_dag
        # GraphDAG(causal_matrix, true_dag)


        # calculate accuracy
        # met = castle.metrics.MetricsDAG(causal_matrix, true_dag)
        met = eval_met(causal_matrix, true_dag)
        logger.info(f"met: {met.metrics}")
        res.append(met.metrics)

        
        logger.info(f"Before pruning: {met2.metrics}") if met2 else logger.info(f"Before pruning: {None}",)
        logger.info(f"After pruning: {met.metrics}")


    keys = res[0].keys()

    averages = {key: [] for key in keys}
    std_devs = {key: [] for key in keys}


    for dictionary in res2:
        for key in keys:
            averages[key].append(dictionary[key])
            std_devs[key].append(dictionary[key])

    for key in keys:
        averages[key] = np.mean(averages[key])
        std_devs[key] = np.std(std_devs[key])

    result2 = {key: f"{averages[key]:.2f}+-{std_devs[key]:.2f}" for key in keys}
    logger.info(f"Before pruning: {result2}")


    averages = {key: [] for key in keys}
    std_devs = {key: [] for key in keys}


    for dictionary in res:
        for key in keys:
            averages[key].append(dictionary[key])
            std_devs[key].append(dictionary[key])

    for key in keys:
        averages[key] = np.mean(averages[key])
        std_devs[key] = np.std(std_devs[key])

    result = {key: f"{averages[key]:.2f}+-{std_devs[key]:.2f}" for key in keys}
    logger.info(f"After pruning: {result}")

