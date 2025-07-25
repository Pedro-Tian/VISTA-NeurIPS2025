python rebuttal_DC_FAS.py --method linear --sem_type gauss --type SF --h 5 --nodes 50 --repeat 1 --model GOLEM 
python rebuttal_DC_FAS.py --method nonlinear --sem_type quadratic --type SF --h 5 --nodes 50 --repeat 1 --model GOLEM 
python rebuttal_baseline.py --method linear --sem_type gauss --type SF --h 5 --nodes 50 --repeat 1 --model GOLEM --normalized 1
python rebuttal_baseline.py --method nonlinear --sem_type quadratic --type SF --h 5 --nodes 50 --repeat 1 --model GOLEM --normalized 1

python rebuttal_DC_FAS.py --method linear --sem_type gauss --type SF --h 5 --nodes 50 --repeat 1 --model SCORE 
python rebuttal_DC_FAS.py --method nonlinear --sem_type quadratic --type SF --h 5 --nodes 50 --repeat 1 --model SCORE 
python rebuttal_baseline.py --method linear --sem_type gauss --type SF --h 5 --nodes 50 --repeat 1 --model SCORE --normalized 1
python rebuttal_baseline.py --method nonlinear --sem_type quadratic --type SF --h 5 --nodes 50 --repeat 1 --model SCORE --normalized 1

python rebuttal_DC_FAS.py --method linear --sem_type gauss --type SF --h 5 --nodes 50 --repeat 1 --model NOTEARS 
python rebuttal_DC_FAS.py --method nonlinear --sem_type quadratic --type SF --h 5 --nodes 50 --repeat 1 --model NOTEARS 
python rebuttal_baseline.py --method linear --sem_type gauss --type SF --h 5 --nodes 50 --repeat 1 --model NOTEARS --normalized 1
python rebuttal_baseline.py --method nonlinear --sem_type quadratic --type SF --h 5 --nodes 50 --repeat 1 --model NOTEARS --normalized 1

python rebuttal_DC_FAS.py --method linear --sem_type gauss --type SF --h 5 --nodes 50 --repeat 1 --model CAM 
python rebuttal_DC_FAS.py --method nonlinear --sem_type quadratic --type SF --h 5 --nodes 50 --repeat 1 --model CAM 
python rebuttal_baseline.py --method linear --sem_type gauss --type SF --h 5 --nodes 50 --repeat 1 --model CAM --normalized 1
python rebuttal_baseline.py --method nonlinear --sem_type quadratic --type SF --h 5 --nodes 50 --repeat 1 --model CAM --normalized 1

python rebuttal_DC_FAS.py --method linear --sem_type gauss --type SF --h 5 --nodes 50 --repeat 1 --model DAGGNN 
python rebuttal_DC_FAS.py --method nonlinear --sem_type quadratic --type SF --h 5 --nodes 50 --repeat 1 --model DAGGNN 
python rebuttal_baseline.py --method linear --sem_type gauss --type SF --h 5 --nodes 50 --repeat 1 --model DAGGNN --normalized 1
python rebuttal_baseline.py --method nonlinear --sem_type quadratic --type SF --h 5 --nodes 50 --repeat 1 --model DAGGNN --normalized 1