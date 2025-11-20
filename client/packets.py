import struct
import math

def compress_packet(state_dict):
    """
    Compresses the Game State dict into a custom binary format.
    Schema:
    [Num Players: uint16]
    FOR EACH PLAYER:
       [UUID Len: uint8] [UUID Bytes]
       [X: float] [Y: float]
       [Angle: uint16 (mapped 0-65535)]
       [Boost: uint8 (0/1)]
       [Length: float]
       [Num Segments: uint16]
       FOR EACH SEGMENT:
          [X: float] [Y: float]
    [Num Food: uint16]
    FOR EACH FOOD:
       [X: float] [Y: float] [Size: uint8]
    """
    data = bytearray()
    
    players = state_dict.get("players", {})
    data.extend(struct.pack("!H", len(players)))
    
    for uuid_str, p_data in players.items():
        uuid_bytes = uuid_str.encode('utf-8')
        data.extend(struct.pack("!B", len(uuid_bytes)))
        data.extend(uuid_bytes)
        
        # Basic Info
        # Map angle 0-2PI to 0-65535 to save 2 bytes
        angle_mapped = int((p_data["angle"] % (2 * math.pi)) / (2 * math.pi) * 65535)
        boost_byte = 1 if p_data["boost"] else 0
        
        data.extend(struct.pack("!ffHBf", 
            p_data["x"], 
            p_data["y"], 
            angle_mapped, 
            boost_byte, 
            p_data["length"]
        ))
        
        # Segments
        segs = p_data["segments"]
        data.extend(struct.pack("!H", len(segs)))
        for seg in segs:
            data.extend(struct.pack("!ff", seg[0], seg[1]))

    # 2. Food
    food_list = state_dict.get("food", [])
    data.extend(struct.pack("!H", len(food_list)))
    
    for f in food_list:
        data.extend(struct.pack("!ffB", f["x"], f["y"], f["size"]))
        
    return bytes(data)
