import base64

def strip_whitespace() -> None:
    svg = open("./svgs/Squeakplump.svg").read()
    svg = svg.replace(" ", "").replace("\n", "").replace("\t", "").replace("\r", "")

def to_base64() -> None:
    svg = open("./svgs/Squeakplump.svg").read()
    print(len(svg))
    svg = base64.b64encode(svg.encode("utf-8")).decode("utf-8")
    print(svg)

to_base64()
