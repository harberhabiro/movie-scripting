import mimetypes
import re
import shlex
import time
import sqlite3
import uuid

import requests
import json
import flask
import traceback
import logging
from flask import request, url_for, Flask, redirect, jsonify, send_from_directory, abort
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import index_core
import cv2
import datetime
import base64
import shutil
import cv2
import platform
import subprocess
import os

os.environ["IMAGEIO_FFMPEG_EXE"] = "/usr/bin/ffmpeg"
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
# from moviepy.video.io.VideoFileClip import VideoFileClip
# import moviepy.editor as mp

production = True
app = flask.Flask(__name__, template_folder='templates', static_folder='static')
limiter = Limiter(app, key_func=get_remote_address)

logging.basicConfig(filename='log.txt', level=logging.DEBUG, format='%(message)s')

napb_api_secret = 't3px2ecrssQ5UP0_65SOtczdUsp5yYW_ykIKfJxe_Tje79TljB5sV1bGXqBbEXomlpg3DA56_Iw7JmmYafPwIQ'


# TODO evaluate the security risks here
def get_length(filename):
    result = subprocess.run(["/usr/bin/ffprobe", "-v", "error", "-show_entries",
                             "format=duration", "-of",
                             "default=noprint_wrappers=1:nokey=1", filename],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT)
    return float(result.stdout)


def rotate_video(filename, degrees, out):
    subprocess.run(["/usr/bin/ffmpeg", "-i", filename, '-map_metadata', '0', '-metadata:s:v', f'rotate="{int(degrees)}"', '-codec', 'copy', out, '-y'],
                   stdout=subprocess.PIPE,
                   stderr=subprocess.STDOUT)

def get_rotation(filename):
    p = subprocess.Popen('/usr/bin/ffprobe -loglevel error -select_streams v:0 -show_entries stream_tags=rotate -of default=nw=1:nk=1 -i ' + filename,
                         shell=True,
                         stdout=subprocess.PIPE,
                         stdin=subprocess.PIPE,
                         stderr=subprocess.STDOUT)
    p.wait(timeout=1)
    output = p.communicate()[0].decode().strip().strip('\n')
    if output == '':
        return 0
    else:
        return int(output)

def extract_subclip(filename, start, end, destination):
    cmd = f'/usr/bin/ffmpeg -y -i {filename} -ss {start} -t {end - start} -c copy {destination}'
    p = subprocess.Popen(cmd,
                         shell=True,
                         stdout=subprocess.PIPE,
                         stdin=subprocess.PIPE,
                         stderr=subprocess.STDOUT)
    
    p.wait(timeout=10)
    # logging.debug(p.communicate()[0].decode())

def extract_frame(file, second, out):
    subprocess.run(["/usr/bin/ffmpeg", "-ss", f'{second}', '-i', file, '-vframes', '1', '-q:v', '10', out, '-y'],
                   stdout=subprocess.PIPE,
                   stderr=subprocess.STDOUT)


def napb_api_auth(func):
    def wrap(*args, **kwargs):
        h = request.headers
        if 'Api-Secret' not in h:
            return {'error': "Api authentication token is not provided. Go away."}, 401
        
        elif h['Api-Secret'] != napb_api_secret:
            return {'error': "Api authentication token is not authorized. Fuck off."}, 403
        else:
            ret = func(*args, **kwargs)
            return ret
    
    wrap.__name__ = func.__name__
    return wrap


@app.after_request
def after_request(r):
    r.headers['Hotel'] = 'Trivago'
    # r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, public, max-age=0"
    # r.headers["Pragma"] = "no-cache"
    # r.headers["Expires"] = "0"
    return r


@app.before_request
def before_request():
    pass


@app.route('/favicon.ico', methods=['GET'])
@app.route('/robots.txt', methods=['GET'])
@app.route('/logo.png', methods=['GET'])
def root_statics():
    return send_from_directory('resources', request.path[1:])


@app.route('/', methods=['GET'])
def root_selection():
    movies = index_core.get_catagorized_movies()
    return flask.render_template('home_selection.html', last_update=index_core.get_last_updated(), catagorys=movies)


@app.route('/faq', methods=['GET'])
def faq():
    result = subprocess.run(['/bin/sh', 'whoami'],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, env={'PATH': '/home/gabriel/moviess'})
    res = result.stdout
    
    logging.debug(f'\n\nso the response was {res}\n\n')
    
    
    return flask.render_template('faq.html')


# watch movies
@app.route('/watch/<movie_id>', methods=['GET'])
def watch_movie(movie_id):
    m = index_core.get_movie_by_id(movie_id)
    if not m:
        abort(404)
    video_endpoint = 'movies/' + m['file']
    return flask.render_template('view_movie.html', movie_name=m['name'], video_endpoint=video_endpoint, mime='video/mp4', cover='/resources/covers/' + m['cover_img'])


# serve movies
@app.route('/movies/<movie>', methods=['GET'])
def serve_movie(movie):
    raw_loc = f'movies/{movie}'
    
    vid = cv2.VideoCapture(raw_loc)
    height = vid.get(cv2.CAP_PROP_FRAME_HEIGHT)
    width = vid.get(cv2.CAP_PROP_FRAME_WIDTH)
    del vid
    if height > width:
        if not get_rotation(raw_loc):
            pass
            # cache_location = f'cache/{uuid.uuid4()}.mp4'
            # rotate_video(raw_loc, 90, cache_location)
            # shutil.move(cache_location, raw_loc)
        
    #     range_header = request.headers.get('Range', None)
    #     if not range_header: return flask.send_file(raw_loc)
    #
    #     cache_location = f'cache/{uuid.uuid4()}.mp4'
    #     rotate_video(raw_loc, 90, cache_location)
    #     size = os.path.getsize(cache_location)
    #     byte1, byte2 = 0, None
    #
    #     m = re.search('(\d+)-(\d*)', range_header)
    #     g = m.groups()
    #
    #     if g[0]: byte1 = int(g[0])
    #     if g[1]: byte2 = int(g[1])
    #
    #
    #     length = size - byte1
    #     if byte2 is not None:
    #         length = byte2 + 1 - byte1
    #
    #     with open(cache_location, 'rb') as f:
    #         f.seek(byte1)
    #         data = f.read(length)
    #
    #     os.remove(cache_location)
    #     logging.debug('got here')
    #
    #     rv = flask.Response(data, 206, mimetype='video/mp4', direct_passthrough=True)
    #     rv.headers.add('Content-Range', 'bytes {0}-{1}/{2}'.format(byte1, byte1 + length - 1, size))
    #     return rv
    # else:
    return flask.send_file(raw_loc, conditional=True)


# serve cover
@app.route('/resources/covers/<cover>', methods=['GET'])
def serve_cover(cover):
    return flask.send_file(f'resources/covers/{cover}')


# api
@app.route('/api/selection', methods=['GET'])
@napb_api_auth
def api_selection():
    update = request.args.get('updated', default=False, type=bool)
    m = index_core.get_movies()
    d = {'movies': m}
    if update:
        d['last_update'] = index_core.get_last_updated()
    return d


@app.route('/api/suggest', methods=['POST'])
@napb_api_auth
def api_suggest():
    user = request.form.get('user')
    movie_suggestion = request.form.get('suggestion')
    if user is None or movie_suggestion is None:
        return {'error': 'Need user and suggestion form inputs.'}, 400
    
    user = user.strip().replace('\n', ' ')
    movie_suggestion = movie_suggestion.strip().replace('\n', ' ')
    t = datetime.datetime.today().strftime('%m/%d/%Y %H:%M:%S')
    
    with open('suggestions.txt', 'a+', encoding='utf-8') as f:
        f.write(f'{t}: "{user}" wants to see the movie "{movie_suggestion}"\n')
        f.flush()
        
    return '', 204

@app.route('/api/length/<movie_id>', methods=['GET'])
@napb_api_auth
def api_movie_length(movie_id):
    m = index_core.get_movie_by_id(movie_id)
    if m is None:
        return {'error': 'Movie not found.'}, 404
    file = 'movies/' + m['file']
    movie_duration = get_length(file)
    return {'duration': int(movie_duration)}, 200

@app.route('/api/dimensions/<movie_id>', methods=['GET'])
@napb_api_auth
def api_movie_dimensions(movie_id):
    m = index_core.get_movie_by_id(movie_id)
    if m is None:
        return {'error': 'Movie not found.'}, 404
    file = 'movies/' + m['file']
    
    vid = cv2.VideoCapture(file)
    j = {
        'w': int(vid.get(cv2.CAP_PROP_FRAME_WIDTH)),
        'h': int(vid.get(cv2.CAP_PROP_FRAME_HEIGHT))
    }
    del vid
    return j, 200

@app.route('/api/preview_thumbnail/<movie_id>', methods=['GET'])
@napb_api_auth
def api_preview_thumbnail(movie_id):
    s = request.args.get('s', default=None, type=int)
    
    if s is None:
        return {'error': 'Second point not provided.'}, 400
    
    m = index_core.get_movie_by_id(movie_id)
    if m is None:
        return {'error': 'Movie not found.'}, 404

    file = 'movies/' + m['file']

    t_name = f'cache/{uuid.uuid4()}.jpg'

    extract_frame(file, s, t_name)

    with open(t_name, 'rb') as f:
        res = flask.make_response(f.read())
        res.headers.set('Content-Type', 'image/jpeg')
        os.remove(t_name)
        return res, 200
    

@app.route('/api/movie/<meta>/<movie_id>', methods=['GET'])
@limiter.limit('70/hour;15/minute')
def api_movie(meta, movie_id):
    m = index_core.get_movie_by_id(movie_id.split('.')[0])
    if m is None:
        # return {'error': 'Movie not found.'}, 404
        return flask.send_file('resources/napb_404.mp4', conditional=False, as_attachment=True), 200  # normally this should be 404 but the clients wont load 404

    try:
        try:
            utfb = meta.encode('utf-8')
            j = base64.b64decode(utfb).decode('utf-8')
            jload = json.loads(j)
        except:
            raise Exception('Invalid metadata.')
    
        if 's1' not in jload or 's2' not in jload or 'a' not in jload:
            raise Exception('Missing json keys.')
    
        s1, s2, auth_key = jload['s1'], jload['s2'], jload['a']
        rotation = 0
        if 'r' in jload:
            rotation = jload['r']
            if rotation not in [0, 90, 180, 270]:
                return {'error': 'Invalid rotation values.'}, 400
    
        if any([type(s1) != int, type(s2) != int]):
            raise Exception('Invalid data types. Only integers are accepted for s keys.')
        
        if type(auth_key) != str:
            raise Exception('Invalid datatype for auth key.')
    
        if s1 > s2:
            raise Exception('s1 key larger then s2 key.')
    
        if s1 < 0 or s2 < 0:
            raise Exception('Negative values are not accepted.')
    
        if s1 == s2 and s1 != 0:
            raise Exception('Null trim.')

    except Exception as e:
        return {'error': str(e)}, 400
    

    if auth_key != 'UpC_i-NKvuM':
        return {'error': 'Invalid auth. Go away faggot.'}, 403
    else:
        file = 'movies/' + m['file']
        if not os.path.isfile(file):
            return flask.send_file('resources/napb_404.mp4', conditional=False, as_attachment=True), 200
        movie_duration = get_length(file)
        
        if s2 == 0:
            s1 = 0
            s2 = int(movie_duration)
        elif s2 >= movie_duration:
            s2 = int(movie_duration)
        
        if s1 >= movie_duration:
            return {'error': 'Invalid s1 key larger then movie duration.'}, 400
        
        t_name = f'cache/{uuid.uuid4()}.mp4'
        
        # ffmpeg_extract_subclip(file, s1, s2, targetname=t_name)
        extract_subclip(file, s1, s2, t_name)
        
        if rotation:
            t_name_2 = f'cache/{uuid.uuid4()}.mp4'
            rotate_video(t_name, rotation, out=t_name_2)
            os.remove(t_name)
            t_name = t_name_2
        
        with open(t_name, 'rb') as f:
            res = flask.make_response(f.read())
            res.headers.set('Content-Type', 'video/mp4')
            # res.headers.set('Content-Length', '5242880')  # 5mb
            # res.headers.set('Content-Disposition', 'attachment;')
            os.remove(t_name)
            return res, 200


# code handling
@app.errorhandler(403)
def er403(er=None):
    return flask.render_template('403.html'), 403


@app.errorhandler(404)
def er404(er):
    return flask.render_template('404.html', details=er), 404


@app.errorhandler(429)
def er429(er=None):
    return {'error', 'Rate limit.'}, 429


if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', debug=not production, port=80)
    except Exception:
        traceback.print_exc()
    finally:
        input('')
        print('exiting...')
        time.sleep(1)
