import time
import index_core
import uuid
from datetime import datetime


def write_time():
    t = datetime.today().strftime('%m/%d/%Y')
    while 1:
        i = input('Would you like to update the "last updated" text? (yes, no): ').lower().strip()
        if i == 'yes':
            index_core.update_edit_time(t)
            break
        elif i == 'no':
            break
        else:
            print('Please enter a valid option.')


while 1:
    print('\n1. Remove movie.')
    print('2. Add movie.')
    print('3. List movies.')
    print('4. Exit.')
    
    try:
        option = int(input('Option: '))
        if option > 4:
            raise Exception
        if option < 1:
            raise Exception
    except Exception:
        print('Please enter a valid option.')
        time.sleep(1)
        continue
    
    if option == 4:
        break
        
    elif option == 1:
        movie_id = input('\nMovie id: ')
        if index_core.get_movie_by_id(movie_id) is None:
            print('This movie doesnt exist to begin with.')
        else:
            index_core.delete_movie(movie_id)
            write_time()
            
    elif option == 2:
        print('')
        print('Place your video file in "movies/"')
        print('Place your cover image in "resources/covers/"')
        
        name = input('Movie name: ')
        while 1:
            file = input('Video file (Ex. "LionKing.mp4"): ')
            if file.startswith('movies/'):
                print('Do not include "movies/". Only the raw file name.')
            else:
                break
        while 1:
            cover = input('Cover image (Ex. "lion_king_cover.png" Default is default.jpg): ')
            if cover.startswith('resources/covers/'):
                print('Do not include "resources/covers/". Only the raw file name.')
            else:
                if cover.strip() == '':
                    cover = 'default.jpg'
                break
                
        cat = input('Category (Case sensitive. Exact spelling or it will be seen as a new Category): ').strip()
        desc = input('Description: ')
        while 1:
            idd = input('Movie id (leave empty to auto decide): ').lower().strip()
            if idd == '':
                idd = str(uuid.uuid4())
            if index_core.get_movie_by_id(idd) is not None:
                print('Try a different id, this one already exists. It needs to be unique.')
                time.sleep(.3)
            else:
                break
        
        d = {
           "name": name,
           "file": file,
           "cover_img": cover,
           "category": cat,
           "description": desc,
           "id": idd
        }
        
        index_core.add_movie(d)
        write_time()
        
        
    elif option == 3:
        print('')
        m = index_core.get_catagorized_movies()
        a = []
        for catag, movies in m.items():
            for i in movies:
                a.append(i)
                
        for i in a:
            name = i['name']
            file = i['file']
            cover = i['cover_img']
            cat = i['category']
            desc = i['description'].replace('\n', ' ')
            idd = i['id']
            print(f'Movie name: {name}\n'
                  f'File: {file}\n'
                  f'Cover image: {cover}\n'
                  f'Category: {cat}\n'
                  f'Description: {desc}\n'
                  f'Movie Id: {idd}\n')
