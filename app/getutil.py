import requests
import json
import argparse

def make_request(url, data):
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'insomnia/9.3.3'
    }
    response = requests.post(url, headers=headers, data=json.dumps(data))
    print(f"Status Code: {response.status_code}")
    try:
        response_json = response.json()
        print("Response JSON:")
        print(json.dumps(response_json, indent=2))
    except requests.exceptions.JSONDecodeError:
        print("Response is not in JSON format. Raw response:")
        print(response.text)

def series(args):
    url = "https://tlmastercontrol.teleosmedia.com/backend/media/topMedia"
    data = {
        "slug": "jltv",
        "typeId": 1,
        "itemsPerPage": 50
    }
    make_request(url, data)

def seasons(args):
    url = "https://tlmastercontrol.teleosmedia.com/backend/media/topMedia"
    data = {
        "slug": "jltv",
        "typeId": 2,
        "itemsPerPage": 50
    }
    make_request(url, data)

def episodes(args):
    url = "https://tlmastercontrol.teleosmedia.com/backend/media/topMedia"
    data = {
        "slug": "jltv",
        "itemsPerPage": 50,
        "typeId": 3,
        "pageNo": args.get("pageNo", 1)
    }
    response = make_request(url, data)
    return response.json() if response and response.status_code == 200 else []

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Fetch media information")
    subparsers = parser.add_subparsers(title="subcommands", dest="subcommand")

    series_parser = subparsers.add_parser("series", help="Fetch series information")

    seasons_parser = subparsers.add_parser("seasons", help="Fetch seasons information")


    episodes_parser = subparsers.add_parser("episodes", help="Fetch episodes information")


    args = parser.parse_args()

    if args.subcommand == "series":
        series(args)
    elif args.subcommand == "seasons":
        seasons(args)
    elif args.subcommand == "episodes":
        episodes(args)
    else:
        parser.print_help()
