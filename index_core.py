import json


def j():
    with open('movie_index.json', 'r') as jj:
        d = json.loads(jj.read())
        return d


def wj(js):
    with open('movie_index.json', 'w') as jj:
        json.dump(js, jj, indent=2)


def get_last_updated():
    return j()['last_update']


def get_movies():
    movies = j()['movies']
    return movies


def get_catagorized_movies():
    m = get_movies()
    d = {}
    for i in m:
        if i['category'] not in d:
            d[i['category']] = []
        d[i['category']].append(i)
    return d


def get_movie_by_id(movie_id):
    for i in get_movies():
        if i['id'] == movie_id:
            return i
    return None


def add_movie(movie):
    if not bool(get_movie_by_id(movie['id'])):
        g = j()
        g['movies'].append(movie)
        wj(g)


def delete_movie(movie_id):
    g = get_movie_by_id(movie_id)
    if g is not None:
        js = j()
        movies = list(js['movies'])
        js['movies'] = []
        
        for i in movies:
            if i['id'] != movie_id:
                js['movies'].append(i)
        wj(js)

def update_edit_time(new_time):
    g = j()
    g['last_update'] = new_time
    wj(g)