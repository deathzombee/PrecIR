# Collection of procedures related to ESLs
# 2018 furrtek - furrtek.org
# See LICENSE

import serial

def terminate_frame(frame, repeats):
    # Compute whole frame's CRC16
    result = 0x8408
    poly = 0x8408

    for by in frame:
        result ^= by
        for bi in range(0, 8):
            if (result & 1):
                result >>= 1
                result ^= poly
            else:
                result >>= 1

    frame.append(result & 255)
    frame.append((result / 256) & 255)
    frame.append(repeats & 255)     # This is used internally, it's not part of the transmitted data

def make_raw_frame(PLID, cmd):
    frame = [0x85, PLID[3], PLID[2], PLID[1], PLID[0], cmd]
    return frame

def make_mcu_frame(PLID, cmd):
    frame = [0x85, PLID[3], PLID[2], PLID[1], PLID[0], 0x34, 0x00, 0x00, 0x00, cmd]
    return frame

def append_word(frame, value):
    frame.append(value / 256)
    frame.append(value & 255)
    
def get_plid(barcode):
    PLID = [0] * 4
    if len(barcode) != 17:
        return PLID
    id_value = int(barcode[2:7]) + (int(barcode[7:12]) << 16)
    PLID[0] = (id_value >> 8) & 0xFF
    PLID[1] = id_value & 0xFF
    PLID[2] = (id_value >> 24) & 0xFF
    PLID[3] = (id_value >> 16) & 0xFF
    return PLID

def make_ping_frame(PLID, repeats):
    frame = make_raw_frame(PLID, 0x97)
    frame.append(0x01)
    frame.append(0x00)
    frame.append(0x00)
    frame.append(0x00)
    for b in range(0, 22):
        frame.append(0x01)
    terminate_frame(frame, repeats)
    return frame

def make_refresh_frame(PLID):
    frame = make_mcu_frame(PLID, 0x01)
    for b in range(0, 22):
        frame.append(0x00)
    terminate_frame(frame, 1)
    return frame

def transmit_frames(frames, port):
    ser = serial.Serial(port, 57600, timeout = 5)    # 5s timeout for read
    ser.reset_input_buffer()
    frame_count = len(frames)
    i = 1
    for fr in frames:
        data_size = len(fr) - 1
        repeats = fr[-1]
        print("Transmitting frame %u/%u, length %u, repeated %u times." % (i, frame_count, data_size, repeats))
    
        ba = bytearray()
        ba.append(data_size)
        ba.append(repeats)
        for b in range(0, len(fr) - 1):
            ba.append(fr[b])
        ser.write(ba)
        ser.flush()
        ser.read_until('A')
        i += 1
    
    ser.close()
