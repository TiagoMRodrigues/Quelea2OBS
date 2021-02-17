import requests
import html.parser
import datetime
import os
import json
from flask import Flask, Response, request, render_template, session, copy_current_request_context
from bs4 import BeautifulSoup, element
from typing import List
from config import *
from time import sleep
from flask_socketio import SocketIO, emit, disconnect

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

bnc = {}
bnc_file = "bible_names_corrector.json"
if os.path.isfile(bnc_file):
    bnc = json.load(open(bnc_file))

class live_obs_show_data():
    def __init__(self):
        self.clear = False
        self.is_bible_on = False
        self.is_music_on = False

        self.parsed_html = None # type: BeautifulSoup

        self.bible_verse = ""
        self.bible_version = ""
        self.bible_ref = ""

        self.music_lyrics = ""
        self.music_name = ""
        self.music_author = ""

        self.sent = False
        self.previous_hash = 0
        self.selected = 0

        self.to_obs_str = ""

    def parse_title(self):
        v = self.parsed_html.find_all('i')   # type: element.ResultSet

        self.bible_version = ""
        self.bible_ref = ""

        self.music_name = ""
        self.music_author = ""

        a = ""
        b = ""

        if len(v) > 0:
            z = v[0].text.split("\n")
            if len(z) >= 2:
                if ":" in z[0]:
                    a = ":".join(z[0].split(":")[1:])
                    b = z[1]

                    if self.is_bible_on:
                        r = a.split(" ")
                        l = " ".join(r[:-1]).strip()
                        c = r[-1]

                        if l in bnc:
                            a = f"{bnc[r[0].strip()]} {c}"

                        self.bible_ref, self.bible_version = a,b

                    else:
                        self.music_name, self.music_author = a,b


        #print(f"title <{a}> self.bible_version <{b}> ")

    def update_bible_or_music(self):
        self.is_bible_on = len(self.parsed_html.find_all("sup")) > 0
        self.is_music_on = not self.is_bible_on

    def update_to_obs_str(self):

        if self.is_bible_on:
            last_verse_index = 0

            for x, y in enumerate(self.to_obs_str):
                last_verse_index = x
                if y not in "0123456789":
                    break

            self.bible_verse = self.to_obs_str[:last_verse_index] + ' - ' + self.to_obs_str[last_verse_index:]

        else:
            self.music_lyrics = " ".join([x for x in self.to_obs_str.rstrip().split(" ") if len(x) > 0])

    def send_to_obs_data(self):
        if self.clear:
            x = {"bible_verse" : "", "bible_version" : "", "bible_ref" : "",
                 "music_lyrics" : "","music_name" : "", "music_author" : "", "type":"CLEAR" }
        else:
            if self.is_bible_on:
                x = {"bible_verse": self.bible_verse, "bible_version": self.bible_version, "bible_ref": self.bible_ref,
                     "music_lyrics": "", "music_name": "", "music_author": "", "type":"BIBLE"}
            else:
                x = {"bible_verse": "", "bible_version": "", "bible_ref": "",
                     "music_lyrics": self.music_lyrics, "music_name": self.music_name, "music_author": self.music_author,
                     "type":"MUSIC"}

        return x

    def send(self, force=False):
        if not self.sent or force:
            socketio.emit('update', self.send_to_obs_data(), broadcast=True)
            self.sent = True



live_obs = live_obs_show_data()

def make_request(request_):
    url = request_.path
    method = request_.method
    headers = dict(request_.headers)
    data = request_.form

    url = f"{quelea_remote}{url}"
    if headers is None:
        headers = {}

    return requests.request(method, url, params=request_.args, stream=True, headers=headers, allow_redirects=False, data=data)


@socketio.on('connect')
def test_connect():
    live_obs.send(force=True)

@app.route('/section<path:slabel>')
def section(slabel: str):
    x = slabel.find("ss")
    section = "0"
    subsection = "0"
    if x == -1:
        r = make_request(request)
        return return_response(r)
    else:
        section = slabel[:x]
        live_obs.selected = int(slabel[x+2:])
        live_obs.sent = False

    return "section <"+section+">subsection <"+subsection+">"


@app.route('/status')
def status():
    r = make_request(request)

    n_blanked = any([x == "true" for x in r.text.split(",")[:3]])

    if n_blanked != live_obs.clear:
        live_obs.clear = n_blanked
        live_obs.send(force=True)

    return Response(r.text, status=r.status_code, headers=dict(r.raw.headers),)


@app.route('/lyrics')
def lyrics():
    live_obs.to_obs_str = ""

    r = make_request(request)
    r.encoding = quelea_encode

    if r.text.__hash__() != live_obs.previous_hash:
        live_obs.previous_hash = r.text.__hash__()
        live_obs.selected = 0
        live_obs.sent = False

    live_obs.parsed_html = BeautifulSoup(r.text, features="html.parser", from_encoding=r.encoding)
    live_obs.update_bible_or_music()
    live_obs.parse_title()

    x = live_obs.parsed_html.find(attrs={"class":"inner current"})
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

    for s in span_list:
        if new_a is None:
            a_attrs = {"onclick":f"""section("{section}ss{len(n_divs)}");"""}
            attrs = {"display":"block"}
            if len(n_divs) == live_obs.selected:
                attrs["style"] = "background-color: #a6F1FF;"
                to_obs = True
            else:
                to_obs = False

            new_a = live_obs.parsed_html.new_tag('a', attrs=a_attrs)
            new_div = live_obs.parsed_html.new_tag('div', attrs=attrs)
            new_a.append(new_div)

        if s.name.lower() == "br":
            counter += 1

        if to_obs and s.name.lower() == "span":
            live_obs.to_obs_str += f"{s.text}\n"

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

    live_obs.update_to_obs_str()
    live_obs.send()

    return Response(live_obs.parsed_html.prettify(), status=r.status_code, headers=dict(r.raw.headers),)


@app.route('/live_obs_html')
def live_obs_html():
    return Response(render_template("live_obs.html"), status=200)

@socketio.on('my event')
def handle_my_custom_event(data):
    emit('my response', data, broadcast=True)

@app.route('/cifras')
def cifras():
    #r = make_request(request)
    #r.encoding = quelea_encode
    r = requests.get(f"{quelea_remote}/chordsv2")
    return Response(render_template("cifras.html"), status=200, mimetype='text/html')


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
    #app.run(host='0.0.0.0',port=port,threaded=True)
    socketio.run(app, host='0.0.0.0', port=8080)


