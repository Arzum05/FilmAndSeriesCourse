import os
import random
from dotenv import load_dotenv
load_dotenv()
import telebot
from telebot import types
import requests

tmdb = os.getenv("TMDB_API")
token = os.getenv("TOKEN")

bot = telebot.TeleBot(token)

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id,'Привет это бот который посоветует тебе фильм или сериал на вечер 💕')

@bot.message_handler(commands=['help'])
def help(message):
    bot.send_message(message.chat.id,'Добро пожаловать на filmsAndSeriesBot\n\n'
                     'Я найду тебе фильм или сериал на вечер\n\n'
                     'Вот список моих комманд:\n'
                     '/start - Запуск бота\n'
                     '/help - все комманды бота\n'
                     '/search - Найти фильм или сериал по названию\n'
                     '/actor_films - Найти фильм или сериал с твоим любимым актером\n'
                     '/genres - Найти фильм или сериал по твоему жанру\n'
                     '/trailer - Посмотреть трейлер фильма\n'
                     '/random - Случайный фильм или сериал')


@bot.message_handler(commands=['search'])
def search(message):
    bot.send_message(message.chat.id,'Напиши название сериала или фильма:')
    bot.register_next_step_handler(message, search_movie)

def search_movie(message):
    name = message.text
    url = f'https://api.themoviedb.org/3/search/multi?api_key={tmdb}&language=ru-RU&query={name}'
    request = requests.get(url).json()

    if not request['results']:
        bot.send_message(message.chat.id,'Ничего не найдено')
        return

    movie = request['results'][0]
    title = movie.get('title') or movie.get('name')
    overview = movie.get('overview', 'Описание отсутствует')
    rating = movie.get('vote_average', 'Рейтинг отсутствует')
    poster = movie.get('poster_path')
    rating = round(rating)

    text = f'{title}\n\nРейтинг: {rating}\n\n{overview}'
    if poster:
        bot.send_photo(message.chat.id, f'https://image.tmdb.org/t/p/w500{poster}',caption=text, parse_mode='Markdown')
    else:
        bot.send_message(message.chat.id,text)

@bot.message_handler(commands=['actor_films'])
def actor_films(message):
    bot.send_message(message.chat.id,'Напиши имя своего любимого актера, и я пришлю тебе фильмы с ним')
    bot.register_next_step_handler(message, find_actor_films)

def find_actor_films(message):
    global rating, overview, title, poster
    actor_name = message.text
    actor_url = f'https://api.themoviedb.org/3/search/person?api_key={tmdb}&language=ru-RU&query={actor_name}'
    request_actor = requests.get(actor_url).json()

    if not request_actor['results']:
        bot.send_message(message.chat.id,'Актер не найден')
        return

    actor = request_actor['results'][0]
    actor_id = actor['id']

    url_films = f'https://api.themoviedb.org/3/person/{actor_id}/movie_credits?api_key={tmdb}&language=ru-RU'
    request_movie = requests.get(url_films).json()
    movies = request_movie.get('cast')

    if not movies:
        bot.send_message(message.chat.id,'Фильмы с этим актером не найдены')
        return

    top5 = movies[:5]

    for movie in top5:
        title = movie.get('title') or movie.get('name')
        overview = movie.get('overview','Описание отсутствует')
        rating = movie.get('vote_average','Рейтинг отсутствует')
        poster = movie.get('poster_path')
        rating = round(rating)

        text = f'{title}\n\nРейтинг: {rating}\n\n{overview}'
        if poster:
            bot.send_photo(message.chat.id,f'https://image.tmdb.org/t/p/w500{poster}',caption=text, parse_mode='Markdown')
        else:
            bot.send_message(message.chat.id,text)

@bot.message_handler(commands=['genres'])
def genres(message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn1 = types.KeyboardButton('Боевик')
    btn2 = types.KeyboardButton('Романтика')
    btn3 = types.KeyboardButton('Фантастика')
    btn4 = types.KeyboardButton('Комедия')
    keyboard.add(btn1, btn2, btn3, btn4)
    bot.send_message(message.chat.id,'Выбери свой любимый жанр:',reply_markup=keyboard)
    bot.register_next_step_handler(message, choose_genres)

def choose_genres(message):
    genre_name = message.text

    genres = {
        "Боевик": "28",
        "Романтика": "10749",
        "Комедия": "35",
        "Фантастика": "878"
    }

    genres_id = genres.get(genre_name)
    if not genres_id:
        bot.send_message(message.chat.id,'Такого жанра нет, выберите другой')
        return

    genres_url = f'https://api.themoviedb.org/3/discover/movie?api_key={tmdb}&language=ru-RU&with_genres={genres_id}'
    genres_request = requests.get(genres_url).json()

    if not genres_request['results']:
        bot.send_message(message.chat.id,'Фильмы не найдены')
        return

    movie = random.choice(genres_request['results'])
    title = movie.get('title') or movie.get('name')
    overview = movie.get('overview')
    rating = movie.get('vote_average','Рейтинг отсутствует')
    poster = movie.get('poster_path')

    text = f'{title}\n\nРейтинг: {rating}\n\n{overview}'
    if poster:
        bot.send_photo(message.chat.id,f'https://image.tmdb.org/t/p/w500{poster}',caption=text, parse_mode='Markdown' )
    else:
        bot.send_message(message.chat.id,text)



@bot.message_handler(commands=['trailer'])
def trailer(message):
    bot.send_message(message.chat.id,'Напиши название фильма и я пришлю тебе трейлер')
    bot.register_next_step_handler(message, search_trailer)

def search_trailer(message):
    film_name = message.text
    url_search = f'https://api.themoviedb.org/3/search/movie?api_key={tmdb}&language=ru-RU&query={film_name}'
    trailer_request = requests.get(url_search).json()

    if not trailer_request['results']:
        bot.send_message(message.chat.id,'Фильм не найден')
        return

    trailer = trailer_request['results'][0]
    trailer_id = trailer['id']

    trailer_url = f'https://api.themoviedb.org/3/movie/{trailer_id}/videos?api_key={tmdb}&language=ru-RU'
    trailer_request = requests.get(trailer_url).json()
    video = trailer_request.get('results')

    if not video:
        bot.send_message(message.chat.id,'Трейлеры не найдены')
        return

    trailer = None
    for vid in video:
        if vid['type'] == 'Trailer' and vid['site'] == 'YouTube':
            trailer = vid
            break

    if not trailer:
        bot.send_message(message.chat.id,'Трейлеры не найдены')
        return

    yt_url = f"https://www.youtube.com/watch?v={trailer['key']}"
    bot.send_message(message.chat.id,f'Вот трейлер фильма {film_name}:\n{yt_url}')


@bot.message_handler(commands=['random'])
def rand(message):

    page = random.randint(1,50)
    rndm_url = f"https://api.themoviedb.org/3/movie/popular?api_key={tmdb}&language=ru-RU&page={page}"

    rndm_request = requests.get(rndm_url).json()
    films = rndm_request.get('results',[])
    if not films:
        bot.send_message(message.chat.id,'Фильм не найден')
        return

    film = random.choice(films)

    title = film.get('title') or film.get('name')
    overview = film.get('overview','Описание отсутствует')
    rating = film.get('vote_average','Рейтинг отсутствует')
    poster = film.get('poster_path')

    text = f'{title}\n\nРейтинг: {rating}\n\n{overview}'
    if poster:
        bot.send_photo(message.chat.id,f'https://image.tmdb.org/t/p/w500{poster}',caption=text, parse_mode='Markdown')
    else:
        bot.send_message(message.chat.id,text)



bot.polling(none_stop=True)
