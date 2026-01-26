import logging
from datetime import datetime

logger = logging.getLogger("MessageValidator")

def validate_message(message: dict) -> bool:
    """
    Valida que el missatge compleixi l'esquema JSON oficial de l'assignatura[cite: 36, 69].
    """
    # 1. Camps obligatoris segons l'especificació [cite: 69, 70, 75]
    required_fields = ["type", "source", "target", "timestamp", "payload", "status"]
    
    if not all(field in message for field in required_fields):
        missing = [f for f in required_fields if f not in message]
        logger.error(f"Validació fallida: Falten camps {missing} [cite: 69]")
        return False

    # 2. Validació del format de temps ISO 8601 UTC [cite: 72]
    try:
        # Accepta el format 2025-10-21T15:30:00Z [cite: 46]
        ts = message["timestamp"]
        if ts.endswith('Z'):
            datetime.fromisoformat(ts.replace('Z', '+00:00'))
        else:
            datetime.fromisoformat(ts)
    except (ValueError, TypeError):
        logger.error(f"Validació fallida: Format de timestamp incorrecte [cite: 72]")
        return False

    # 3. Validació de tipus de missatges coneguts [cite: 70]
    valid_types = [
        "map.v1", "inventory.v1", "materials.requirements.v1", 
        "build.v1", "command.start.v1", "command.pause.v1", 
        "command.stop.v1", "command.resume.v1"
    ]
    if message["type"] not in valid_types and not message["type"].startswith("command."):
        logger.warning(f"Tipus de missatge desconegut: {message['type']} [cite: 70]")
        # Podem deixar-lo passar o ser estrictes

    return True