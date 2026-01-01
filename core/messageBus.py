import asyncio
import logging

class MessageBus:
    def __init__(self):
        # El diccionari de cues emmagatzema una cua per a cada agent
        self.queues = {} 
        self.logger = logging.getLogger("MessageBus")

    def subscribe(self, agent_id: str):
        """Crea una cua per a un nou agent."""
        if agent_id not in self.queues:
            new_queue = asyncio.Queue()
            self.queues[agent_id] = new_queue
            self.logger.info(f"Agent '{agent_id}' subscrit al Bus.")
            return new_queue
        return self.queues[agent_id]

    async def publish(self, message: dict):
        """Envia un missatge a l'agent de destí (target)."""
        target = message.get("target")
        if target in self.queues:
            # Aquí aniria la VALIDACIÓ JSON
            self.queues[target].put_nowait(message)
            self.logger.debug(f"Missatge publicat a {target}: {message['type']}")
            # Aquí aniria el LOGGING PERSISTENT del missatge
        else:
            self.logger.warning(f"Error: Agent de destí '{target}' no trobat.")