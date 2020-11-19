import requests
import html.parser

from flask import Flask, Response, request
from bs4 import BeautifulSoup, element
from typing import List
from config import *

app = Flask(__name__)

update_file = False
selected = 0
previous_hash = 0
print_to_file = True


def make_request(request_):
    url = request_.path
    method = request_.method
    headers = dict(request_.headers)
    data = request_.form

    url = f"{quelea_remote}{url}"
    if headers is None:
        headers = {}

    return requests.request(method, url, params=request_.args, stream=True, headers=headers, allow_redirects=False, data=data)


@app.route('/section<path:slabel>')
def section(slabel: str):
    global selected
    global print_to_file

    x = slabel.find("ss")
    section = "0"
    subsection = "0"
    if x == -1:
        r = make_request(request)
        return return_response(r)
    else:
        section = slabel[:x]
        selected = int(slabel[x+2:])
        print_to_file = True
    return "section <"+section+">subsection <"+subsection+">"


@app.route('/lyrics')
def hello_world():
    global selected
    global previous_hash
    global print_to_file

    r = make_request(request)
    r.encoding = quelea_encode

    if r.text.__hash__() != previous_hash:
        previous_hash = r.text.__hash__()
        selected = 0
        print_to_file = True


    parsed_html = BeautifulSoup(r.text, features="html.parser", from_encoding=r.encoding)
    x = parsed_html.find(attrs={"class":"inner current"})
    p = x.findChildren(name='p')[0] # type: element.Tag
    f_on_c = p.attrs["onclick"]
    section = f_on_c.split("(")[1].split(")")[0]
    span_list = [s for s in p.children]  # type: List[element.Tag]
    p.clear()
    n_divs = []
    counter = 0
    new_a = None
    new_div = None
    to_obs = False
    to_obs_str = ""
    for s in span_list:
        if new_a is None:
            a_attrs = {"onclick":f"""section("{section}ss{len(n_divs)}");"""}
            attrs = {"display":"block"}
            if len(n_divs) == selected:
                attrs["style"] = "background-color: #a6F1FF;"
                to_obs = True
            else:
                to_obs = False

            new_a = parsed_html.new_tag('a', attrs=a_attrs)
            new_div = parsed_html.new_tag('div', attrs=attrs)
            new_a.append(new_div)


        if s.name.lower() == "br":
            counter += 1


        if to_obs and s.name.lower() == "span":
            to_obs_str += f"{s.text}\n"

        new_div.append(s)

        if counter == n_lines:
            n_divs.append(new_a)
            new_a = None
            new_div = None
            counter = 0

    if new_a is not None:
        n_divs.append(new_a)

    for d in n_divs:
        p.append(d)

    if print_to_file:
        with open(file_location, "w") as f:
            print(to_obs_str.strip(), file=f)
            print_to_file = False

    return Response(parsed_html.prettify(), status=r.status_code, headers=dict(r.raw.headers),)

def return_response(r):
    headers = dict(r.raw.headers)

    def generate():
        for chunk in r.raw.stream(decode_content=False):
            yield chunk

    out = Response(generate(), headers=headers)
    out.status_code = r.status_code

    return out

@app.errorhandler(404)
def proxy(e):
    r = make_request(request)
    return return_response(r)

if __name__ == '__main__':
    app.run(host='0.0.0.0',port=port)