import base64
import json
import os


def strip_whitespace(svg: str) -> str:
    svg = svg.replace("\n", "")
    return svg

def pack_svgs() -> list:
    output = []
    base_dir = "./svgs/"
    for file in os.listdir('./svgs/'):
        svg = strip_whitespace(open(f"{base_dir}{file}").read())
        svg = base64.b64encode(svg.encode("utf-8")).decode("utf-8")
        print(file)
        name, mtype = file.split("_")
        mtype = mtype[0:-3]
        print(name, mtype)
        return

def pack_metadata() -> list:
    metadata = json.loads(open("./server/moves.json").read())
    print(metadata)


pack_svgs()
