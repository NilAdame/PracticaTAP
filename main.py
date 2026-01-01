# --- main.py (VERSIÓ CORREGIDA) ---

import asyncio
import logging
from mcpi.minecraft import Minecraft
from mcpi import block
import time

# Importa els teus mòduls
from agents.MinerBot import MinerBot
from core.messageBus import MessageBus
from BaseAgent import State 
# Assumeixo que tens un fitxer BaseAgent.py amb l'Enum State

# Configuració del Logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("MAIN")


# --- DEFINICIÓ DE L'ID D'AGENT (ÚS CONSISTENT) ---
# Si l'ID al bus és 'MinerBot_A', l'encaminador ha de retornar 'MinerBot_A'.
TARGET_MINER_ID = "MinerBot_A"


# --- 1. Funcions de Connexió ---

def connect_to_minecraft():
    """Estableix la connexió a la instància de Minecraft."""
    # ... (la teva lògica de connexió, sense canvis)
    try:
        mc = Minecraft.create()
        mc.postToChat("Multi-Agent System Activated!")
        logger.info("Connexió a Minecraft establerta.")
        return mc
    except Exception as e:
        logger.error(f"ERROR: No es pot connectar al servidor de Minecraft. {e}")
        return None

# El logger ha de ser el logger principal si no es defineix un nou.
parser_logger = logging.getLogger("PARSER") 

# --- 2. Parser de Comandes (Versió ÚNICA i RobustA) ---

def parse_command(chat_message: str):
    """
    Analitza el text cru d'una comanda del xat i extreu l'Agent Destí, 
    la Comanda d'Acció i els Paràmetres.
    """
    parts = chat_message.strip().split()
    
    if not parts or not parts[0].startswith('/'):
        return None, None, None

    prefix = parts[0][1:].lower() 
    command = "help" 
    agent_name = None
    param_start_index = -1
    
    # --- Lògica d'Encaminament (Routing) ---
    
    if prefix == 'miner':
        # CAS MÉS COMÚ: /miner start x=10 y=50
        agent_name = TARGET_MINER_ID # <--- ÚS DE L'ID GLOBAL CONSISTENT
        command = parts[1].lower() if len(parts) >= 2 else "help"
        param_start_index = 2
        
    elif prefix == 'agent':
        # CAS GENÈRIC: /agent status o /agent miner start
        
        # /agent [command] (p. ex., /agent start)
        if len(parts) >= 2 and parts[1].lower() in ['start', 'pause', 'stop', 'status', 'help']:
            agent_name = TARGET_MINER_ID
            command = parts[1].lower()
            param_start_index = 2
        
        # /agent [target] [command] (p. ex., /agent miner status)
        elif len(parts) >= 3 and parts[1].lower() == 'miner':
            agent_name = TARGET_MINER_ID
            command = parts[2].lower()
            param_start_index = 3
        
        # Si només és /agent
        else:
            agent_name = TARGET_MINER_ID
            command = "help"
            
    else:
        parser_logger.warning(f"Prefix de comanda desconegut: {prefix}")
        return None, None, None


    # --- Extreure Paràmetres (Clau=Valor) ---
    params = {}
    if param_start_index != -1:
        for part in parts[param_start_index:]:
            if '=' in part:
                key, value = part.split('=', 1)
                try:
                    params[key] = int(value)
                except ValueError:
                    params[key] = value

    parser_logger.info(f"PARSE EXIT: Agent={agent_name}, Cmd={command}, Params={params}")
    return agent_name, command, params


# --- 3. Bucle Asíncron de Lectura del Xat ---

async def chat_listener_loop(mc: Minecraft, bus: MessageBus):
    """Bucle asíncron per a llegir el xat i processar comandes."""
    parser_logger.info("Iniciant escolta asíncrona de comandes del xat.")
    
    CHECK_INTERVAL = 0.05 
    
    while True:
        try:
            start_time = time.monotonic()
            
            posts = mc.events.pollChatPosts() 
            
            for post in posts:
                # La comanda s'ha d'interceptar, fins i tot si és 'Unknown command' al MC
                agent_name, command, params = parse_command(post.message)

                if agent_name and command:
                    # L'ID de l'agent i el 'target' del bus han de coincidir (MinerBot_A)
                    control_message = {
                        "type": f"command.{command}.v1",
                        "source": "User", 
                        "target": agent_name, # Aquest és el nom que el Bus utilitzarà
                        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                        "payload": params,
                        "status": "PENDING",
                        "context": {"source_chat": post.message}
                    }
                    await bus.publish(control_message)
                
            elapsed_time = time.monotonic() - start_time
            sleep_time = max(0, CHECK_INTERVAL - elapsed_time)
            await asyncio.sleep(sleep_time) 

        except Exception as e:
            parser_logger.error(f"Error crític en el listener del xat: {e}")
            break


# --- 4. Funció Principal (main) ---

async def main():
    mc_connection = connect_to_minecraft()
    if not mc_connection:
        return

    # Inicialitzar el sistema de comunicació
    bus = MessageBus()

    # Creació i Registre dels Agents
    miner_id = TARGET_MINER_ID # "MinerBot_A"
    miner_queue = bus.subscribe(miner_id)
    
    # L'agent necessita la connexió mcpi per actuar
    miner_agent = MinerBot(agent_id=miner_id, message_bus=bus, input_queue=miner_queue, mc_connection=mc_connection)
    
    # Llista de tasques asíncrones a executar concurrentment
    tasks = [
        asyncio.create_task(chat_listener_loop(mc_connection, bus)),
        asyncio.create_task(miner_agent.run())
    ]

    logger.info("Totes les tasques asíncrones s'estan executant.")
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.warning("Sistema interromput per l'usuari (Ctrl+C). Tancant.")