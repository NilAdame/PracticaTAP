import asyncio
import logging
import importlib
import pkgutil
import time

from mcpi.minecraft import Minecraft

# Importem mòduls del projecte
import agents 
from missatges.messageBus import MessageBus
from agents.BaseAgent import BaseAgent
import sys
import os

# Afegeix la carpeta actual al path per a que trobi 'agents', 'strategies', etc.
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 1. Configuració de Logging [cite: 19, 214]
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(name)s | %(message)s')
logger = logging.getLogger("MAIN")

TARGET_MINER_ID = "MinerBot-1"

# --- 2. Parser de Comandes (Lògica de Xat)

def parse_command(chat_message: str):
    parts = chat_message.strip().split()
    if not parts: return None, None, None

    first_word = parts[0].lower()
    prefix = first_word[1:] if first_word.startswith('/') else first_word

    agent_name = None
    command = "help"
    params = {}

    # MAPPING DE PREFIXOS A IDS REALS
    if prefix == 'explorer':
        agent_name = "ExplorerBot-1"
    elif prefix == 'miner':
        agent_name = "MinerBot-1"
    elif prefix == 'builder': 
        agent_name = "BuilderBot-1"
    
    if agent_name:
        command = parts[1].lower() if len(parts) >= 2 else "help"

    # Extraiem paràmetres x=100 z=100 etc.
    for part in parts[1:]: 
        if '=' in part:
            k, v = part.split('=', 1)
            params[k] = int(v) if v.isdigit() else v

    return agent_name, command, params
async def chat_listener_loop(mc: Minecraft, bus: MessageBus):
    """Bucle asíncron que llegeix el xat de Minecraft i publica al Bus[cite: 33, 152]."""
    logger.info("Iniciant escolta asíncrona...")
    while True:
        try:
            posts = mc.events.pollChatPosts() 
            for post in posts:
                # AFEGEIX AIXÒ PER VEURE-HO TOT:
                print(f"DEBUG XAT REBUT: {post.message}") 
                
                agent_name, command, params = parse_command(post.message)
                if agent_name and command:
                    control_message = {
                        "type": f"command.{command}.v1",
                        "source": "User", 
                        "target": agent_name, 
                        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                        "payload": params,
                        "status": "PENDING",
                        "context": {"source_chat": post.message}
                    }
                    await bus.publish(control_message)
            await asyncio.sleep(0.1) 
        except Exception as e:
            logger.error(f"Error en el listener del xat: {e}")
            break

# --- 3. Descobriment Reflectiu  ---

def discover_agents():
    found_classes = {}
    for _, name, _ in pkgutil.iter_modules(agents.__path__):
        module = importlib.import_module(f"agents.{name}")
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (isinstance(attr, type) and issubclass(attr, BaseAgent) and attr is not BaseAgent):
                found_classes[attr_name] = attr
                logger.info(f"REFLEXIÓ: '{attr_name}' registrat automàticament.")
    return found_classes

# --- 4. Main Loop ---

async def main():
    mc = Minecraft.create() 
    bus = MessageBus()
    agent_classes = discover_agents()
    
    active_agents = []
    tasks = []

    mapping = {
        "ExplorerBot": "ExplorerBot-1",
        "MinerBot": "MinerBot-1",
        "BuilderBot": "BuilderBot-1"
    }

    for class_name, agent_id in mapping.items():
        if class_name in agent_classes:
            queue = bus.subscribe(agent_id)
            agent_inst = agent_classes[class_name](
                agent_id=agent_id, 
                mc_connection=mc, 
                message_bus=bus, 
                input_queue=queue
            )
            active_agents.append(agent_inst)
            tasks.append(asyncio.create_task(agent_inst.run()))

    # Afegim el listener del xat a les tasques asíncrones 
    tasks.append(asyncio.create_task(chat_listener_loop(mc, bus)))

    logger.info("SISTEMA ACTIU: Escoltant xat i agents corrent.")

    try:
        await asyncio.gather(*tasks)
    except asyncio.CancelledError:
        logger.info("Aturant el sistema...")
    finally:
        for agent in active_agents:
            agent.handle_control("stop") 

if __name__ == "__main__":
    asyncio.run(main())