"""Assistant reactions are a local file operation, separate from browser authorship."""
from pathlib import Path
import argparse,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from board.environment import use_project_environment
if __name__=='__main__':use_project_environment(__file__)
from board import agent_tools
from board.app import REACTIONS
p=argparse.ArgumentParser();p.add_argument('agent',choices=['Claude','GPT']);p.add_argument('message_id');p.add_argument('emoji',choices=list(REACTIONS));p.add_argument('--remove',action='store_true');p.add_argument('--enough',action='store_true');p.add_argument('--root',type=Path,default=ROOT/'data');a=p.parse_args()
try:agent_tools.react_message(a.root,a.agent,a.message_id,a.emoji,remove=a.remove,enough=a.enough)
except ValueError as error:p.error(str(error))
print('Reaction saved')
