# custom code
from custom_collector import FastPyDroneSimCollector
from gym_sim import Drone_Sim

# tianshou code
from tianshou.policy import SACPolicy, BasePolicy
from tianshou.utils.net.continuous import ActorProb, Critic, RecurrentActorProb, RecurrentCritic
from tianshou.utils.net.common import Net
from tianshou.data import VectorReplayBuffer,HERVectorReplayBuffer,PrioritizedVectorReplayBuffer
from tianshou.trainer import OffpolicyTrainer
from tianshou.highlevel.logger import LoggerFactoryDefault
from tianshou.utils import WandbLogger

# spiking specific code
from spiking_gym_wrapper import SpikingEnv
from spikingActorProb import SpikingNet

import torch
import os
# set wandb in debug mode
import wandb
# wandb.init(mode='disabled')

# torch.cuda.set_device(0)
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
# device = torch.device('cpu')
if device == torch.device('cuda'):
    gpu = True
else:   
    gpu = False
print('Device in use:', device)
def create_policy():
    # create the networks behind actors and critics
    net_a = Net(state_shape=observation_space,
                hidden_sizes=[64,64], device=device)
    net_c1 = Net(state_shape=observation_space,action_shape=action_space,
                    hidden_sizes=[64,64],
                    concat=True,device=device)
    net_c2 = Net(state_shape=observation_space,action_shape=action_space,
                    hidden_sizes=[64,64],
                    concat=True,device=device)

    # create actors and critics
    actor = ActorProb(
        net_a,
        action_space,
        unbounded=True,
        conditioned_sigma=True,
        device=device
    )
    critic1 = Critic(net_c1, device=device)
    critic2 = Critic(net_c2, device=device)

    # create the optimizers
    actor_optim = torch.optim.Adam(actor.parameters(), lr=1e-3)
    critic_optim = torch.optim.Adam(critic1.parameters(), lr=1e-3)
    critic2_optim = torch.optim.Adam(critic2.parameters(), lr=1e-3)

    # create the policy
    policy = SACPolicy(actor=actor, actor_optim=actor_optim, \
                        critic=critic1, critic_optim=critic_optim,\
                        critic2=critic2, critic2_optim=critic2_optim,\
                        action_space=env.action_space,\
                        observation_space=env.observation_space, \
                        action_scaling=True, device=device) # make sure actions are scaled properly
    return policy

def create_spiking_policy():
    # create the networks behind actors and critics
    net_a = SpikingNet(state_shape=observation_space, action_shape=action_space,
                hidden_sizes=[64,64], device=device, repeat=6)
    net_c1 = Net(state_shape=observation_space,action_shape=action_space,
                    hidden_sizes=[64,64],
                    concat=True,device=device)
    net_c2 = Net(state_shape=observation_space,action_shape=action_space,
                    hidden_sizes=[64,64],
                    concat=True,device=device)

    # create actors and critics
    actor = ActorProb(
        net_a,
        action_shape=action_space,
        unbounded=True,
        conditioned_sigma=True,
        device=device
    )
    critic1 = Critic(net_c1, device=device)
    critic2 = Critic(net_c2, device=device)

    # create the optimizers
    actor_optim = torch.optim.Adam(actor.parameters(), lr=1e-3)
    critic_optim = torch.optim.Adam(critic1.parameters(), lr=1e-3)
    critic2_optim = torch.optim.Adam(critic2.parameters(), lr=1e-3)

    # create the policy
    policy = SACPolicy(actor=actor, actor_optim=actor_optim, \
                        critic=critic1, critic_optim=critic_optim,\
                        critic2=critic2, critic2_optim=critic2_optim,\
                        action_space=env.action_space,\
                        observation_space=env.observation_space, \
                        action_scaling=True).cuda() # make sure actions are scaled properly
    return policy, net_a

def create_recurrent_policy():
    # create actors and critics
    actor = RecurrentActorProb(
        layer_num=2,
        state_shape=observation_space,
        action_shape=action_space,
        hidden_layer_size=64,
        device=device,
        unbounded=True
    )

    critic1 = RecurrentCritic(
        layer_num=2,
        state_shape=observation_space,
        action_shape=action_space,
        hidden_layer_size=64,
        device=device,
    )
    critic2 = RecurrentCritic(
        layer_num=2,
        state_shape=observation_space,
        action_shape=action_space,
        hidden_layer_size=64,
        device=device,
    )

    # create the optimizers
    actor_optim = torch.optim.Adam(actor.parameters(), lr=1e-3)
    critic_optim = torch.optim.Adam(critic1.parameters(), lr=1e-3)
    critic2_optim = torch.optim.Adam(critic2.parameters(), lr=1e-3)

    # create the policy
    policy = SACPolicy(actor=actor, actor_optim=actor_optim, \
                        critic=critic1, critic_optim=critic_optim,\
                        critic2=critic2, critic2_optim=critic2_optim,\
                        action_space=env.action_space,\
                        observation_space=env.observation_space, \
                        action_scaling=True).cuda() # make sure actions are scaled properly
    return policy

# define training args
args = {
      'epoch': 1e2,
      'step_per_epoch': 5e3,
      'step_per_collect': 5e3, # 2.5 s
      'test_num': 50,
      'update_per_step': 10,
      'batch_size': 256,
      'wandb_project': 'FastPyDroneGym',
      'resume_id':1,
      'logger':'wandb',
      'algo_name': 'sac',
      'task': 'stabilize',
      'seed': int(3),
      'logdir':'',
      'spiking':True,
      'recurrent':False,
      'logger': 'wandb',
      }

# define number of drones to be simulated
if not gpu:
    N_envs = 100
else:
    blocks = 32
    threads = 8
    N_envs = blocks*threads
# N_envs = 100
if args['recurrent']:
    # define action buffer True to encapsulate action history in observation space
    env = Drone_Sim(N_drones=N_envs, action_buffer=False,test=False, gpu=False, device=device)
    test_env = Drone_Sim(N_drones=1, action_buffer=False, test=True, gpu=False, device=device)

    observation_space = env.observation_space.shape or env.observation_space.n
    action_space = env.action_space.shape or env.action_space.n

    policy = create_recurrent_policy()

    # create buffer (stack_num defines the number of sequenctial samples)
    buffer=PrioritizedVectorReplayBuffer(total_size=200000,buffer_num=N_envs, stack_num=64, alpha=0.4, beta=0.6)
else:
    # define action buffer True to encapsulate action history in observation space
    env = Drone_Sim(N_drones=N_envs, action_buffer=True,test=False, gpu=False, device=device)
    test_env = Drone_Sim(N_drones=10, action_buffer=True, test=True, gpu=False, device=device)

    observation_space = env.observation_space.shape or env.observation_space.n
    action_space = env.action_space.shape or env.action_space.n

    if args['spiking']:
        policy, spikingnet = create_spiking_policy()
        env = SpikingEnv(env, spikingnet)
        test_env = SpikingEnv(test_env,spikingnet)
    else:
        policy = create_policy()
    
    
    # create buffer (stack_num defines the number of sequenctial samples)
    # buffer=PrioritizedVectorReplayBuffer(total_size=200000,buffer_num=N_envs, stack_num=1, alpha=0.4, beta=0.6)
    buffer=VectorReplayBuffer(total_size=200000,buffer_num=N_envs, stack_num=1)
if not device == torch.device('cpu'):
    policy = policy.cuda()
print('\nI was working on figuring out how to get data on GPU before training, Batch has to_torch_ where you can pass device as well\n')
# create the parallel train_collector, which is optimized to gather custom vectorized envs
train_collector = FastPyDroneSimCollector(policy=policy, env=env, buffer=buffer, device=device)
train_collector.reset()
test_collector = FastPyDroneSimCollector(policy=policy,env=test_env, device=device)
# define a number of start timesteps to fill buffer (now one sec of data *100 drones )
train_collector.collect(n_step=N_envs*100)

# log
import datetime
now = datetime.datetime.now().strftime("%y%m%d-%H%M%S")
# args['algo_name = "sac"
current_path = os.path.dirname(os.path.abspath(__file__))
log_path = os.path.join(current_path,args['logdir'], args['task'], "sac")
from tianshou.utils import WandbLogger
from torch.utils.tensorboard import SummaryWriter

logger = WandbLogger()
writer = SummaryWriter(log_path)
writer.add_text("args", str(args))
logger.load(writer)

def save_best_fn(policy: BasePolicy, log_path='') -> None:
    torch.save(policy.state_dict(), os.path.join(log_path, "policy.pth"))

print('Observation space: ', observation_space)
print('Action space: ', action_space)


print("Start training")
# trainer
result = OffpolicyTrainer(
    policy=policy,
    train_collector=train_collector,
    test_collector=test_collector, # no testing performed 
    max_epoch=args['epoch'],
    step_per_epoch=args['step_per_epoch'],
    step_per_collect=args['step_per_collect'],
    episode_per_test=args['test_num'],
    batch_size=args['batch_size'],
    save_best_fn=save_best_fn,
    logger=logger,
    update_per_step=args['update_per_step'],
    test_in_train=False,
    buffer=buffer,).run()
    

# print with nice formatting
import pprint
pprint.pprint(result)