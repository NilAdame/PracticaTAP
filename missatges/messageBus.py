import asyncio
import json
import logging
from datetime import datetime

logger = logging.getLogger("MessageBus")

class MessageBus:
    def __init__(self):
        # Diccionario de colas: { "AgentID": asyncio.Queue() }
        self.subscriptions = {}
        # Sistema de bloqueos para minería: { "(x,z)": "AgentID" }
        self.locks = {} 

    def subscribe(self, agent_id):
        """Registra un agente y le asigna una cola de entrada."""
        self.subscriptions[agent_id] = asyncio.Queue()
        logger.info(f"Subscripció confirmada per a: {agent_id}")
        return self.subscriptions[agent_id]

    async def publish(self, message):
        required = ["type", "source", "target", "timestamp", "payload", "status"]
        if not all(k in message for k in required):
            logger.error(f"FAIL: Camps obligatoris absents a {message}")
            return False

        # 2. Validació de format de temps ISO 8601 UTC [cite: 72]
        try:
            datetime.fromisoformat(message["timestamp"].replace('Z', '+00:00'))
        except (ValueError, TypeError):
            logger.error(f"FAIL: Timestamp invàlid ({message.get('timestamp')})")
            return False

        target = message["target"]
        
        # 3. Lògica d'entrega asíncrona i no bloquejant [cite: 139]
        if target == "broadcast":
            # Segons l'enunciat, el BuilderBot pot fer broadcast per sincronitzar estat global 
            for agent_id, queue in self.subscriptions.items():
                if agent_id != message["source"]:
                    await queue.put(message)
            logger.info(f"BROADCAST: {message['type']} enviat a tots.")
            return True

        if target in self.subscriptions:
            await self.subscriptions[target].put(message)
            logger.info(f"DELIVERED: {message['type']} de {message['source']} a {target}") 
            return True
        
        logger.warning(f"NOT FOUND: Destinatari {target} no registrat.")
        return False
        
    def request_lock(self, agent_id, sector_coords):
        """Permite a un MinerBot bloquear una zona (x, z)."""
        if sector_coords not in self.locks:
            self.locks[sector_coords] = agent_id
            return True
        return self.locks[sector_coords] == agent_id

    def release_locks(self, agent_id):
        """Libera todos los bloqueos de un agente (al hacer STOP/ERROR)."""
        initial_count = len(self.locks)
        self.locks = {k: v for k, v in self.locks.items() if v != agent_id}
        logger.info(f"Alliberats bloquejos per a {agent_id}") 