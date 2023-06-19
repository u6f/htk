import httpx, csv, re, time, hashlib, argparse, string, random

print("★ htk - Simple CLI Utility to export/import hanime.tv playlists ★")
parser = argparse.ArgumentParser()
parser.add_argument("-m", "--Mode", help = "e/i (Export or Import)")
parser.add_argument("-l", "--Login", help = "Login credentials for importing")
parser.add_argument("-s", "--Source", help = ".csv file for importing")
parser.add_argument("-p", "--Playlist", help = "Link to playlist")
args = parser.parse_args()


def sha256(text): # sha256 hasher
    return hashlib.sha256(str(text).encode()).hexdigest()

def headers(session_token): # Make X-/Auth headers
    t = str(int(time.time()))
    return {
        "X-Session-Token"    : session_token,
        "X-Signature-Version": "web2",
        "X-Time"             : t,
        "X-Signature"        : sha256(f"9944822{t}8{t}113"),
        "X-Token"            : "null"
    }


def login(email: str, password: str): # Log into hanime.tv
    request = httpx.post("https://www.universal-cdn.com/rapi/v4/sessions", json={
        "burger": email,
        "fries" : password
    }, headers=headers(""))
    if request.status_code == 200:
        response = request.json()
        return response['session_token']
    else:
        raise exit(f"[-] Login failed! Recheck your credentials and/or try again. | Status code: {request.status_code} | Response: {request.text}")


def parse_playlist(url):
    csv_formatted = []
    if re.compile(r"https://hanime\.tv/playlists/([A-Za-z]+([0-9]+[A-Za-z]+)+)", re.IGNORECASE).match(url):
        slug = url.split("/")[4]
        playlist = httpx.get("https://hanime.tv/rapi/v7/playlists/"+slug)
        if playlist.status_code == 200:
            playlist = playlist.json()['playlist']
            id = playlist['id']
            name = playlist['slug']
            size = playlist['count']
            print(f"[I] {url} has {size} videos.")
            videos = httpx.get(f"https://hanime.tv/api/v8/playlist_hentai_videos?playlist_id={id}&__order=sequence,DESC&__offset=0&__count={size}", headers=headers(""))
            for i in videos.json()['fapi']['data']:
                url = f"https://hanime.tv/videos/hentai/"+i['slug']
                id = i['id']
                size = size - 1
                print(f"[+] ({size + 1}) {url}")
                csv_formatted.append([id, url])
            return csv_formatted, name
        else:
            raise exit("[-] 404'd, sure that's a valid playlist?")
    else:
        raise exit("[-] Invalid link. (According to regex)")

def export(videos: list, name: str):
    with open(name+'.csv', 'w+', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['ID', 'URL'])
        writer.writerows(videos)
        print(f"[+] Wrote {len(videos)} videos to {name}.csv")
    file.close()
    input("Hit Enter to exit. . .")

def imp(session_token, file):
    rows = []
    with open(file, "r") as f:
        reader = csv.reader(f)
        for row in reader:
            rows.append(row)
    f.close()
    rows.pop(0)
    rows.reverse()
    title = "★ github.com/u6f/htk ~ "+"".join(random.sample(string.digits+string.ascii_letters, 5))
    create_playlist = httpx.post("https://hanime.tv/rapi/v7/playlists", headers=headers(session_token), json={
        "title": title,
        "visibility": "unlisted",
    })
    for x in create_playlist.json()['playlists']:
        if x['title'] == title:
            slug = x['slug']
            id = x['id']
            break
    print("[I] Made playlist @ https://hanime.tv/playlists/"+slug)
    for x in rows:
        add = httpx.post("https://hanime.tv/api/v8/playlist_hentai_videos", headers=headers(session_token), json={
            "playlist_id": id,
            "hentai_video_id": x[0]
        }).json()
        print(f"[+] {x[1]} / #{add['sequence']+1}")
    input("Hit Enter to exit. . .")


try:
    if args.Mode.lower() in ['e', 'export'] and args.Playlist:
        i, o = parse_playlist(args.Playlist)
        export(i, o)
    elif args.Mode.lower() in ['i', 'import'] and args.Login and args.Source:
        args.Login = args.Login.split(":")
        session_token = login(args.Login[0], args.Login[1])
        imp(session_token, args.Source)
except:
    print("[ Example usage ]\nExporting: htk.py -m e -p https://hanime.tv/playlists/g8cxzutl7dvgzaxposff\nImporting: htk.py -m i -l email:password -s g8cxzutl7dvgzaxposff.csv")


# https://hanime.tv/rapi/v7/playlists/g8cxzutl7dvgzaxposff