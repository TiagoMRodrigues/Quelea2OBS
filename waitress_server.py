from waitress import serve
from paste.translogger import TransLogger
import main

serve(TransLogger(main.app), host='0.0.0.0',port=8080, threads=16)