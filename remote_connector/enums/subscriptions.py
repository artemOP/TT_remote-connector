from enum import Enum


class EventSubscriptions(Enum):
    enable_map_data_relay = "enableMapDataRelay"  # enables all events
    enable_position = "enablePosition"  # sends a position update every 100ms with [x, y, z, heading]
    enable_players = "enablePlayers"  # sends a players event back every 100ms with [[x, y, z], ...]
    enable_peds = "enablePeds"  # sends a peds event back every 400ms with [[x, y, z], ...]
    enable_blips = "enableBlips"  # sends a blips event every 30s with [[x, y, z, sprite, colour, alpha, type], ...]
    enable_chat = "enableChat"  # sends a chat event when a chat message is received, data may depend on message
