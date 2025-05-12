# VISTA-NeurIPS2025
This is an anonymous code submission for our paper.

# Installation
```
conda create -n py310 python==3.10
pip install --upgrade pip
pip install gcastle numpy scipy torch pygam cdt igraph sfas
```
## Install dodiscover
```
git clone https://github.com/py-why/dodiscover.git
cd dodiscover
pip install -e .
```
# Run Baseline
One can run the baseline by
```
python baseline.py --model NOTEARS --nodes 100 --h 5 --type ER 
```
This is an example that generates ER5 graph with 100 nodes, and solve it by base learner names NOTEARS.

# Run VISTA
To test our proposed method, one can run the code by
```
python DC_FAS.py --model GOLEM --nodes 100 --h 5 --type SF
```
This is an example that generated SF5 graph with 100 nodes, and solve it by our proposed divide-and-conquer framework with base learner GOLEM
