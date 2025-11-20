import struct
import math

def compress_packet(state_dict):
    """
    Compresses Game State with Little Endian (<) and 4-byte alignment padding.
    """
    data = bytearray()
    
    players = state_dict.get("players", {})
    # Write Player Count (2 bytes)
    data.extend(struct.pack("<H", len(players)))
    # PADDING: Align to 4 bytes (we are at offset 2, need 2 more)
    data.extend(b'\x00\x00')
    
    for uuid_str, p_data in players.items():
        uuid_bytes = uuid_str.encode('utf-8')
        u_len = len(uuid_bytes)
        
        # 1. Write UUID Len (1 byte) and UUID Bytes
        data.extend(struct.pack("<B", u_len))
        data.extend(uuid_bytes)
        
        # PADDING: Calculate bytes needed to reach next 4-byte boundary
        # Current chunk size = 1 (len) + u_len
        pad_needed = (4 - (1 + u_len) % 4) % 4
        data.extend(b'\x00' * pad_needed)
        
        # 2. Write Basic Info
        # Angle mapped 0-65535
        angle_mapped = int((p_data["angle"] % (2 * math.pi)) / (2 * math.pi) * 65535)
        boost_byte = 1 if p_data["boost"] else 0
        
        # X(4), Y(4) -> Aligned
        # Angle(2), Boost(1) -> Total 3 bytes. Need 1 byte pad after.
        data.extend(struct.pack("<ffHB", 
            p_data["x"], 
            p_data["y"], 
            angle_mapped, 
            boost_byte
        ))
        
        # PADDING: Align after Boost (we are 3 bytes into a 4-byte word)
        data.extend(b'\x00') 

        # 3. Write Length (float is 4 bytes) -> Aligned
        data.extend(struct.pack("<f", p_data["length"]))
        
        # 4. Segments
        segs = p_data["segments"]
        data.extend(struct.pack("<H", len(segs)))
        
        # PADDING: Align after Segment Count (2 bytes) -> Need 2 bytes
        data.extend(b'\x00\x00')

        for seg in segs:
            data.extend(struct.pack("<ff", seg[0], seg[1]))

    # 3. Food
    food_list = state_dict.get("food", [])
    data.extend(struct.pack("<H", len(food_list)))
    
    # PADDING: Align after Food Count (2 bytes) -> Need 2 bytes
    data.extend(b'\x00\x00')
    
    for f in food_list:
        # X(4), Y(4), Size(1) -> Total 9 bytes.
        # Next struct needs to start on 4-byte boundary. 
        # 9 % 4 = 1. We need 3 bytes of padding.
        data.extend(struct.pack("<ffB", f["x"], f["y"], f["size"]))
        data.extend(b'\x00\x00\x00')
    
    # Add Header
    return b'GAMEDATA' + bytes(data)
