import sys, requests, pprint, os, json
from dotenv import load_dotenv

load_dotenv()
USERNAME = os.environ.get("USERNAME")
OUTPUT_PATH = os.environ.get("OUTPUT_PATH")
OUTPUT_FILE = os.path.basename(OUTPUT_PATH) if OUTPUT_PATH else "output.json"
TYPES_RAW = os.environ.get("TYPES")

# endpoints
BASE = "https://trainlog.me"
LEADERBOARD_API = BASE + "/getLeaderboardUsers/"
ALL = "all"
TRAIN = "train"
BUS = "bus"
AIRPLANE = "air"
FERRY = "ferry"
AERIALWAY = "aerialway"
METRO = "metro"
TRAM = "tram"

VALID_KINDS = {
    "all": ALL,
    "train": TRAIN,
    "bus": BUS,
    "airplane": AIRPLANE,
    "ferry":FERRY,
    "aerialway":AERIALWAY,
    "metro":METRO,
    "tram": TRAM
    }        

# select which types to fetch in the .env, defaults to 'all' when not set or invalid
def parse_types(raw):
    parts = [p.strip().lower() for p in raw.split(",") if p.strip()]
    if not parts:
        return ["all"]
    # keep only valid keys, preserve order
    valid = [p for p in parts if p in VALID_KINDS]
    return valid if valid else ["all"]

SELECTED_KINDS = parse_types(TYPES_RAW)

# fetch leaderboard json
def fetch_leaderboard(session, soort):
    url = LEADERBOARD_API + soort
    try:
        r = session.get(url, timeout=20)
    except requests.RequestException as e:
        print("Couldn't get leaderboard:", e)
        return None

    if r.status_code == 200:
        try:
            return r.json()
        except ValueError:
            print("Response doesn't seem to be JSON. Response text:")
            print(r.text[:1000])
            return None
    else:
        print("Couldn't get leaderboard:", r.status_code)
        print("Response snippet:", r.text[:500])
        return None

# print filtered data to terminal
def print_leaderboard_data(data, USERNAME, trip_type="all"):
    if not isinstance(data, dict) or "leaderboard_data" not in data:
        print("Incorrect filestructure or 'leaderboard_data' is missing:")
        pprint(data)
        return

    filtered = [item for item in data["leaderboard_data"] if item.get("username") == USERNAME]

    if not filtered:
        print(f"Couldn't find results for '{USERNAME}'.")
        return
    
    for it in filtered:
        length = it.get("length", 0)
        length_km = round(length / 1_000, 0) if length else "N/A"
        trips = it.get("trips", "N/A")
        print(f"Type: {trip_type} — km: {length_km} — trips: {trips}")

# export filtered data to json
def export_to_json(results, USERNAME):
    def extract_user_data(dataset):
        if not dataset or "leaderboard_data" not in dataset:
            return None
        for item in dataset["leaderboard_data"]:
            if item.get("username") == USERNAME:
                return {
                    "km": round(item.get("length", 0) / 1_000, 0),
                    "trips": item.get("trips", 0)
                }
        return None

    out = {}
    for kind, dataset in results.items():
        out[kind] = extract_user_data(dataset)

    path = OUTPUT_PATH or OUTPUT_FILE
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print(f"Succesfully updated {os.path.basename(path)}")

def main():
    s = requests.Session()
    # fetch selected kinds into a dict keyed by kind name
    results = {}
    for kind in SELECTED_KINDS:
        endpoint = VALID_KINDS.get(kind, ALL)
        data = fetch_leaderboard(s, endpoint)
        if data is None:
            print("No data retrieved.")
            sys.exit(1)
        results[kind] = data

    print(f"Output for user {USERNAME}:")
    for kind in SELECTED_KINDS:
        print_leaderboard_data(results.get(kind), USERNAME, trip_type=kind)

    export_to_json(results, USERNAME)

if __name__ == "__main__":
    main()