import sys
import csv
import math

R = 6371000.0          
ARRIVE_DIST = 3.0     
STOP_SPEED = 0.5      
GREEN_SECONDS = 5


def haversine(lat1, lon1, lat2, lon2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = p2 - p1
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    a = min(1.0, max(0.0, a))
    return 2 * R * math.asin(math.sqrt(a))


def to_float(text):
    """Convert text to a real number, or return None if it is bad."""
    try:
        x = float(text)
    except (TypeError, ValueError):
        return None
    if math.isnan(x) or math.isinf(x):
        return None
    return x


def valid_position(lat, lon):
    return (lat is not None and lon is not None
            and -90 <= lat <= 90 and -180 <= lon <= 180)


def read_targets(path):
    """Read targets. Works with 'lat,lon' or 'target,lat,lon' layouts:
    the header (if any) says which columns are lat and lon; otherwise
    the last two columns are used."""
    targets = []
    lat_col, lon_col = -2, -1
    try:
        with open(path, newline="") as f:
            for row in csv.reader(f):
                cells = [c.strip().lower() for c in row]
                if "lat" in cells and "lon" in cells:     
                    lat_col, lon_col = cells.index("lat"), cells.index("lon")
                    continue
                if len(row) < 2:
                    continue
                try:
                    lat, lon = to_float(row[lat_col]), to_float(row[lon_col])
                except IndexError:
                    continue
                if valid_position(lat, lon):
                    targets.append((lat, lon))
    except OSError:
        pass
    return targets


def main():
    if len(sys.argv) < 3:
        print("usage: python light.py mission_log.csv targets.csv")
        return

    targets = read_targets(sys.argv[2])
    target_idx = 0

    prev_t = None
    prev_lat = prev_lon = None
    green_until = None     
    last_mode = "MANUAL"

    try:
        f = open(sys.argv[1], newline="")
    except OSError:
        print("cannot open log file")
        return

    with f:
        for row in csv.reader(f):
            if len(row) < 2:
                continue
            t_text = row[0].strip()
            t = to_float(t_text)
            if t is None:                    
                continue

            mode = row[1].strip().upper()
            if mode in ("AUTO", "MANUAL"):
                last_mode = mode
            else:
                mode = last_mode             
            lat = to_float(row[2].strip()) if len(row) > 2 else None
            lon = to_float(row[3].strip()) if len(row) > 3 else None
            has_pos = valid_position(lat, lon)

 
            speed = None
            if has_pos and prev_lat is not None and t > prev_t:
                speed = haversine(prev_lat, prev_lon, lat, lon) / (t - prev_t)

            in_green = green_until is not None and t < green_until

            if in_green:
                light = "green"
            else:
                light = "red" if mode == "AUTO" else "blue"
                if (mode == "AUTO" and has_pos and speed is not None
                        and target_idx < len(targets)):
                    tlat, tlon = targets[target_idx]
                    dist = haversine(lat, lon, tlat, tlon)
                    if dist <= ARRIVE_DIST and speed < STOP_SPEED:
                        light = "green"
                        green_until = t + GREEN_SECONDS
                        target_idx += 1

            print(f"{t_text},{light}")

            if has_pos:
                if prev_t is None or t > prev_t:
                    prev_t, prev_lat, prev_lon = t, lat, lon


main()