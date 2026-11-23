import socket
import struct
import math
import csv

HOST = ""
PORT = 2368            
CSV_FILENAME = "scan.csv"

VERTICAL_ANGLES = [-16, -8, 0, 8, -15, -7, 1, 9, -14, -6, 2, 10, -13, -5, 3, 11, -12, -4, 4, 12, -11, -3, 5, 13, -10, -2, 6, 14, -9, -1, 7, 15]
DISTANCE_UNIT = 0.004 

def calculate_xyz(distance_m, azimuth_deg, laser_id):
    vert_angle_deg = VERTICAL_ANGLES[laser_id]
    alpha = math.radians(vert_angle_deg)
    theta = math.radians(azimuth_deg)
    
    X = distance_m * math.cos(alpha) * math.sin(theta)
    Y = distance_m * math.cos(alpha) * math.cos(theta)
    Z = distance_m * math.sin(alpha)
    return X, Y, Z

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((HOST, PORT))
    print("Лидар готов. Не двигайте его!")
    print("Запись начнется автоматически...")

    with open(CSV_FILENAME, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["X", "Y", "Z", "Intensity"])
        
        frame_count = 0
        last_azimuth = 0
        total_points = 0
        
        try:
            while True:
                data, _ = sock.recvfrom(2048)
                if len(data) != 1212: continue
                
                first_flag = struct.unpack_from('<H', data, 0)[0]
                if first_flag != 0xEEFF and first_flag != 0xFFEE: continue
                
                for block_i in range(12):
                    offset = block_i * 100
                    az_raw = struct.unpack_from('<H', data, offset + 2)[0]
                    azimuth = az_raw / 100.0
                    
                    if azimuth < last_azimuth and last_azimuth > 350:
                        frame_count += 1
                        print(f"Записан оборот {frame_count}/50")
                    last_azimuth = azimuth

                    if frame_count >= 50:
                        raise KeyboardInterrupt

                    channel_offset_start = offset + 4
                    for laser_id in range(32):
                        base = channel_offset_start + (laser_id * 3)
                        dist_raw = struct.unpack('<H', data[base : base + 2])[0]
                        intensity = data[base + 2] 
                        
                        distance_m = dist_raw * DISTANCE_UNIT
                        
                        if 0.5 < distance_m < 100:
                            X, Y, Z = calculate_xyz(distance_m, azimuth, laser_id)
                            
                            writer.writerow([f"{X:.3f}", f"{Y:.3f}", f"{Z:.3f}", intensity])
                            total_points += 1

        except KeyboardInterrupt:
            print(f"\nЗаписано {total_points} точек в '{CSV_FILENAME}'")
        finally:
            sock.close()

if __name__ == "__main__":
    main()