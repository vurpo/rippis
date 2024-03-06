import subprocess
import aiohttp
from aiohttp import web
import discid
import musicbrainzngs
import json
import pprint
import asyncio
import os

pp = pprint.PrettyPrinter()

musicbrainzngs.set_useragent("rippis", "0.0", "vurpo@vurpo.fi")

#discid = "3kZ8XDTrJkqoVMbNSRBBQ7dT40E-"
#discid = "1ndha6L7TAnT7aOJAnCrdZkGJhE-"
#discid = "F4WLPtEt251ZoxcLUaGwZwHkeFk-"
#discid = "uUf7XsBON0mo5AWEJTkOv6oaYHM-"

def get_alternatives(disc):
    alternatives = []
    meta = musicbrainzngs.get_releases_by_discid(disc.id, includes=["recordings", "artist-credits"])

    for release in meta['disc']['release-list']:
        for medium in release['medium-list']:
            if medium_has_disc(medium, disc.id, len(disc.tracks)):
                alternatives.append(convert_medium(release, medium))
    
    return alternatives

def medium_has_disc(medium, discid, tracks):
    for disc in medium['disc-list']:
        if disc['id'] == discid and len(medium['track-list']) == tracks:
            return True
    return False

def convert_medium(release, medium):
    converted = {
        "album": {
            "ARTIST": release['artist-credit-phrase'],
            "TITLE": release['title'],
            "DATE": release['date']
        }
    }
    for track in medium['track-list']:
        converted[track['number'].zfill(2)] = convert_track(release, track)
    
    return converted

def convert_track(release, track):
    converted = {
        "ARTIST": track['artist-credit-phrase'],
        "ALBUM": release['title'],
        "DATE": release['date'],
        "TITLE": track['recording']['title'],
        "TRACKNUM": track['number'].zfill(2)
    }
    if release['artist-credit-phrase'] != track['artist-credit-phrase']:
        converted['ALBUMARTIST'] = release['artist-credit-phrase']
    return converted

STATE = set()
WEBSOCKET = None
ALTERNATIVES = None
RIP_OUTPUT = ""
METADATA_FUTURE = None

async def set_state(state):
    STATE.add(state)
    if WEBSOCKET is not None:
        await WEBSOCKET.send_json({"set_state":state})

async def remove_state(state):
    STATE.remove(state)
    if WEBSOCKET is not None:
        await WEBSOCKET.send_json({"remove_state":state})

async def replace_state(remove, add):
    STATE.remove(remove)
    STATE.add(add)
    if WEBSOCKET is not None:
        await WEBSOCKET.send_json({"remove_state":remove, "set_state":add})

async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    global WEBSOCKET
    WEBSOCKET = ws
    global RIP_OUTPUT

    initial_state = {
        "state":list(STATE),
        "rip_log":RIP_OUTPUT}
    global ALTERNATIVES
    if ALTERNATIVES is not None:
        initial_state['alternatives'] = ALTERNATIVES
    await ws.send_json(initial_state)

    async for msg in ws:
        if msg.type == aiohttp.WSMsgType.TEXT:
            try:
                data = msg.json()
                if 'metadata' in data and METADATA_FUTURE is not None:
                    METADATA_FUTURE.set_result(data['metadata'])
            except:
                pass
        elif msg.type == aiohttp.WSMsgType.ERROR:
            print('ws connection closed with exception %s' %
                  ws.exception())

    WEBSOCKET = None
    print('websocket connection closed')

    return ws

async def rip_disc():
    process = await asyncio.create_subprocess_exec('whipper', 'cd', 'rip', '-O', '.', '--track-template', 'rip/%t', '--disc-template', 'rip/rip',
                        stdout=subprocess.PIPE,
                        bufsize=1,
                        universal_newlines=True)
    while (line := str(await process.stdout.readline())) != '':
        print(line)
        global RIP_OUTPUT
        RIP_OUTPUT += line
        global WEBSOCKET
        await WEBSOCKET.send_json({"rip_log_line":line})
    
    await process.communicate()
    if process.returncode != 0:
        raise "Ripping didn't exit normally!"
    
    await remove_state("ripping_disc")
    return

def write_metadata_file(tracknum, meta):
    with open(f"{tracknum}.meta", "w") as file:
        for key, value in meta.items():
            file.write(f"{key}={value}\n")

def check_rips_exist(tracks):
    for track in tracks:
        if not os.path.isfile(f"rip/{track}.flac"):
            return False
    return True

def tag_file(audio_file, meta_file):
    print(f"tagging file {audio_file} from {meta_file}")
    process = subprocess.run(["metaflac", f"--import-tags-from={meta_file}", audio_file],
                             stderr=subprocess.STDOUT,
                             text=True)
    if process.returncode != 0:
        raise "metaflac didn't complete normally!"
    print(process.stdout)

async def start():
    if len(os.listdir(".")) != 0 :
        print("Working directory must be empty! I will rip into this directory")
        return
    
    app = web.Application()
    app.add_routes([web.get('/', websocket_handler)])
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 9999)
    await site.start()

    try:
        await set_state("waiting_for_disc")
        disc = None
        print("waiting for disc")
        while disc == None:
            try:
                disc = discid.read()
            except discid.disc.DiscError:
                await asyncio.sleep(1)
        await replace_state("waiting_for_disc", "getting_metadata")
        print("getting metadata for disc")
        global ALTERNATIVES
        ALTERNATIVES = get_alternatives(disc)
        rip = asyncio.create_task(rip_disc())
        await set_state("ripping_disc")
        print(f"got {len(ALTERNATIVES)} alternatives")
        global WEBSOCKET
        if WEBSOCKET is not None:
            await WEBSOCKET.send_json({"alternatives":ALTERNATIVES})
        global METADATA_FUTURE
        METADATA_FUTURE = asyncio.get_event_loop().create_future()
        await replace_state("getting_metadata", "waiting_for_metadata")
        print("waiting for websocket to choose metadata")
        chosen_metadata = await METADATA_FUTURE
        await remove_state("waiting_for_metadata")
        print(f"websocket chose {chosen_metadata}")
        for key, value in chosen_metadata.items():
            write_metadata_file(key, value)
        await rip
        print(f"ripping complete")
        await set_state("tagging")
        if not check_rips_exist(chosen_metadata.keys()):
            raise "All rips don't exist!"
        for key in chosen_metadata.keys():
            tag_file(f"rip/{key}.flac", f"{key}.meta")
        await remove_state("tagging")

        print("completed!")
    finally:
        await WEBSOCKET.close()
        await runner.cleanup()

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(start())