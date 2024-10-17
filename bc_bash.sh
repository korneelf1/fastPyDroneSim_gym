python BC.py --slope 2 --surrogate-scheduling --device 'cuda:1' --hidden-sizes  256 128 
python BC.py --slope 2  --device 'cuda:1' --hidden-sizes  256 128 
python BC.py --slope 25 --device 'cuda:1 ' --hidden-sizes  256 128 
python BC.py --slope 50 --device 'cuda:1 ' --hidden-sizes  256 128 
python BC.py --slope 100 --device 'cuda:1 ' --hidden-sizes  256 128

python TD3BC.py --slope=2 --device='cuda:1' --hidden-sizes  256 128 --curriculum
python TD3BC.py --slope=25 --device='cuda:1' --hidden-sizes  256 128 --curriculum
python TD3BC.py --slope=100 --device='cuda:1' --hidden-sizes  256 128 --curriculum
python TD3BC.py --slope=200 --device='cuda:1' --hidden-sizes  256 128 --curriculum
python TD3BC.py --slope=2 --surrogate-scheduling --device='cuda:1' --hidden-sizes  256 128 --curriculum

python TD3BC_Online.py --slope=2 --device='cuda:1' --hidden-sizes  256 128 --curriculum
python TD3BC_Online.py --slope=25 --device='cuda:1' --hidden-sizes  256 128 --curriculum
python TD3BC_Online.py --slope=100 --device='cuda:1' --hidden-sizes  256 128 --curriculum
python TD3BC_Online.py --slope=200 --device='cuda:1' --hidden-sizes  256 128 --curriculum
python TD3BC_Online.py --slope=2 --surrogate-scheduling --device='cuda:1' --hidden-sizes  256 128 --curriculum












