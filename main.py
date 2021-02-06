import requests
import html.parser
import datetime

from flask import Flask, Response, request
from bs4 import BeautifulSoup, element
from typing import List
from config import *
from time import sleep

app = Flask(__name__)

update_file = False
selected = 0
previous_hash = 0
print_to_file = True
timestamps = {}
splited_lines = []
to_obs_str = ""
to_obs_ref = ""
current_timestamp = datetime.datetime.now()
blanked = "some value"
bible = "some value"
title = ""
bversion = ""

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


@app.route('/status')
def status():
    global blanked
    global current_timestamp
    r = make_request(request)
    n_blanked = any([x == "true"for x in r.text.split(",")[:3]])

    if n_blanked != blanked:
        blanked = n_blanked
        current_timestamp = datetime.datetime.now()

    return  Response(r.text, status=r.status_code, headers=dict(r.raw.headers),)


@app.route('/lyrics')
def lyrics():
    global selected
    global previous_hash
    global print_to_file
    global splited_lines
    global to_obs_str
    global current_timestamp
    global bible
    global title
    global bversion
    to_obs_str = ""


    r = make_request(request)
    r.encoding = quelea_encode

    if r.text.__hash__() != previous_hash:
        previous_hash = r.text.__hash__()
        selected = 0
        print_to_file = True


    parsed_html = BeautifulSoup(r.text, features="html.parser", from_encoding=r.encoding)

    bible = len(parsed_html.find_all("sup")) > 0

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
    title = ""
    bversion = ""

    v = parsed_html.find_all('i') # type: element.Tag
    if len(v) > 0:

        z = v[0].text.split("\n")
        if len(z) >= 2:
            if ":" in z[0]:
                title = ":".join(z[0].split(":")[1:])
                bversion = z[1]
        else:
            title = z[0]
            bversion = ""                 

    print(f"title <{title}> bversion <{bversion}> ")
    
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

        splited_lines = to_obs_str.split("\n")
        for line_ in range(n_lines):
            fline = ".".join(file_location.split(".")[:-1])+str(line_ + 1)+'.'+file_location.split(".")[-1]
            with open(fline, "w") as f:
                write_this = ""
                if len(splited_lines) > line_:
                    write_this = splited_lines[line_]
                print(write_this, file=f)

        print_to_file = False
        current_timestamp = datetime.datetime.now()

    return Response(parsed_html.prettify(), status=r.status_code, headers=dict(r.raw.headers),)



@app.route('/cifras')
def cifras():
    #r = make_request(request)
    #r.encoding = quelea_encode
    
    r = requests.get(f"{quelea_remote}/chordsv2")

    tbr = f"""
    <html>
    <head>
    <title>Agradece ao teu irmão</title>
    <style>
        span.chord{{
          color: red;
        }}

        div.inner{{
            margin-bottom: 25px;
            border-bottom: 1px;
            border-style: none;
            border-bottom-style: solid;
        }}
        div.current{{
            background-color: #a6F1FF;
        }}


        #zoomable{{
           overflow-x: visible;
          white-space: nowrap;
              
          }}


        #content{{
            left: 15px;
            position: fixed;
            overflow: visible;
            -moz-transform-origin: top left;
            -ms-transform-origin: top left;
            -o-transform-origin: top left;
            -webkit-transform-origin: top left;
             transform-origin: top left;
            -moz-transition: all .2s ease-in-out;
            -o-transition: all .2s ease-in-out;
            -webkit-transition: all .2s ease-in-out;
             transition: all .2s ease-in-out;
        }}
    </style>
    <script src="http://code.jquery.com/jquery-latest.min.js" type="text/javascript"></script>
    <script language="javascript" type="text/javascript">

    var timeout = setInterval(reloadChat, 1000);    
    function reloadChat () {{

         $('#content').load('/chordsv2');


            var width = document.getElementById('content').offsetWidth + 5;
            var height = document.getElementById('content').offsetHeight +5;
            var windowWidth = $(document).outerWidth();
            var windowHeight = $(document).outerHeight();
            var r = 1;
            r = Math.min(windowWidth / width, windowHeight / height)

            $('#content').css({{
                '-webkit-transform': 'scale(' + r + ')',
                '-moz-transform': 'scale(' + r + ')',
                '-ms-transform': 'scale(' + r + ')',
                '-o-transform': 'scale(' + r + ')',
                'transform': 'scale(' + r + ')'
            }});

    }}
    
    </script>
    
    </head>
    <body>
    <div id="zoomable">
        <div id="content">
            {r.text}
        </div>
    </div>
    </body>
    </html>

    """
    return Response(tbr, status=200, mimetype='text/html')



@app.route('/live_obs/<identifier>/<portion>')
def live_obs(identifier, portion):
    global timestamps
    global current_timestamp
    global splited_lines
    global to_obs_str
    global blanked
    global bible

    n = datetime.datetime.now()
    timeout = True
    while((datetime.datetime.now() - n).total_seconds() < 10):
        if identifier not in timestamps or timestamps[identifier] < current_timestamp:
            timeout = False
            break

        sleep(.1)

    if timeout == False:
        timestamps[identifier] = current_timestamp
    
    tbr = ""
    if blanked:
        tbr = ""
    elif portion == "bible":
        if bible:
            
            last_verse_index = 0

            for x,y in enumerate(to_obs_str):
                last_verse_index = x
                if y not in "0123456789":
                    break


            tbr = to_obs_str[:last_verse_index] + ' - ' + to_obs_str[last_verse_index:]  

        else:
            tbr = ""
    elif portion == "ref":
        if bible:
            tbr = title.split(":")[0]
        else:
            tbr = ""

    elif portion == "bible_version":
        if bible:
            tbr = bversion 
        else:
            tbr = ""

    elif portion.lower() == 'all':
        if bible:
            tbr = ""
        else:
            tbr = to_obs_str
    else:
        if portion.isnumeric():
            p_int = int(portion)

            tlines = request.args.get("tlines", 0)
            p_total = int(tlines)

            print(len(splited_lines) , (p_int -1) , p_int , 0)
            
            if p_total > 0 and p_total == sum([1 for _x in splited_lines if len(_x.strip()) > 0 ]) :
                if bible:
                    tbr = ""
                else:
                    tbr = splited_lines[p_int - 1] 

            if p_total == 0 and (p_int -1) < len(splited_lines)  and p_int > 0:
                if bible:
                    tbr = ""
                else:
                    tbr = splited_lines[p_int - 1] 


    return Response(tbr, status=200, mimetype='text/plain')



@app.route('/live_obs_html/<identifier>/<portion>')
def live_obs_html(identifier, portion):
    global timestamps
    global current_timestamp
    global splited_lines
    global to_obs_str
    global blanked
    global bible

    n = datetime.datetime.now()
    timeout = True

    if portion != 'first':
	    while((datetime.datetime.now() - n).total_seconds() < 10):
	        if identifier not in timestamps or timestamps[identifier] < current_timestamp:
	            timeout = False
	            break

	        sleep(.1)

	    if timeout == False:
	        timestamps[identifier] = current_timestamp
    
    verse = ""  
    ref = ""
    version = ""
    music = ""
    verse_svg = ""

    if blanked:
	    verse = ""  
	    ref = ""
	    version = ""
	    music = ""
    elif bible:
        last_verse_index = 0

        for x,y in enumerate(to_obs_str):
            last_verse_index = x
            if y not in "0123456789":
                break

        verse = to_obs_str[:last_verse_index] + ' - ' + to_obs_str[last_verse_index:]  
        
        verse = "\n".join([f"{x}" for x in verse.split("/n")])
        
        verse_svg = f"""<svg width="100%" height="100%">
                            <text id="rectResize" class="wrap" height="100%" width="100%">{verse}</text>
						</svg> """

        ref = title.split(":")[0]
        ref = "\n".join([f"<p>{x}</p>" for x in ref.split("/n")])

        version = bversion
        version = "\n".join([f"<p>{x}</p>" for x in version.split("/n")])


    else:
        music = splited_lines
        music = "\n".join([f"<p>{x}</p>" for x in music if len(x) > 0])

    content = f"""
    				<div id='verse'>
    					{verse_svg}
    				</div>
    				<div id='music'>
    					<div id='music_content'>
	    				     {music}
	    				</div>
    				</div>
    				<div id='ref'>
    					{ref}
    				</div>
    				<div id='version'>
						{version}
    				</div>
    """


    if portion == 'content':
    	return Response(content, status=200)

    tbr = f"""
    	<html>
    		<head>

	    		<script src="https://ajax.googleapis.com/ajax/libs/jquery/3.5.1/jquery.min.js"></script>
	    		<script src="https://d3js.org/d3.v4.min.js"></script>
                <script src="https://d3plus.org/js/d3.js"></script><!-- https: added -->
                <script src="https://d3plus.org/js/d3plus.js"></script><!-- https: added -->
    			<script>
    				verse_size_w = 500;
					verse_size_h = 500;
					$(document).ready(function(){{
					  	verse_size_w = $('#verse').width();
						verse_size_h = $('#verse').height();
						redraw();
						console.log("f1 in 10ms");
    					setTimeout(f1, 10);

					}});
					
					function redraw(){{
					    d3plus.textwrap().container(d3.select('#rectResize')).width(verse_size_w).height(verse_size_h).valign("middle").y(0).resize(true).draw();
					}}

    				function f1(){{
    					$("#content").load("/live_obs_html/{identifier}/content", function(response, status){{
    						if ($("#rectResize").length > 0){{
    							redraw();
    						}}
    						setTimeout(f1, 10);    					
							console.log("f1 in 10ms");
    					}});

    				}}
    				
    				
    			</script>
    		</head>
    		<body>
    			<div id='content' >
    				{ content }
    			</div>
    		</body>
    	</html>
    """


    return Response(tbr, status=200)



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
    app.run(host='0.0.0.0',port=port,threaded=True)