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

user_data = {}

@bot.message_handler(commands=['start'])
def start(message):
    user_data[message.chat.id] = {}
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    keyboard.add("Боевик","Комедия","Романтика","Фантастика")
    bot.send_message(message.chat.id, "Привет,давай подберем фильм по твоим предпочтениями,выбери жанр:",reply_markup=keyboard)
    bot.register_next_step_handler(message,ab_actor)

def ab_actor(message):
    user_data[message.chat.id]["genre"] = message.text
    bot.send_message(message.chat.id,"Укажи любимого актера,или напиши нет",reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(message,new_film)

def new_film(message):
    actor_name = message.text
    user_data[message.chat.id]["actor"] = None if actor_name.lower() == "нет" else actor_name
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("Новый","Любой")
    bot.send_message(message.chat.id,"Хочешь новые фильмы или любые?",reply_markup=keyboard)
    bot.register_next_step_handler(message,film_series)

def film_series(message):
    user_data[message.chat.id]["new"] = message.text
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("Фильм","Сериал")
    bot.send_message(message.chat.id,"Что больше предпочитаешь?",reply_markup=keyboard)
    bot.register_next_step_handler(message,ab_rating)

def ab_rating(message):
    user_data[message.chat.id]["type"] = message.text
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("Топовый","Случайный")
    bot.send_message(message.chat.id,"Предпочитаешь топовые фильмы или это не важно?",reply_markup=keyboard)
    bot.register_next_step_handler(message,fin)

def fin(message):
    user_data[message.chat.id]["rating"] = message.text
    bot.send_message(message.chat.id,"Отлично,теперь я знаю твои предпочтения")

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


@bot.message_handler(commands=['recommend'])
def recommend(message):
    prefs = user_data.get(message.chat.id, {})
    if not prefs:
        bot.send_message(message.chat.id,"Сначала используй /start, чтобы указать свои предпочтения")
        return
    send_movie_by_pref(message.chat.id, prefs)


@bot.message_handler(commands=['random'])
def rndm(message):
    # prefs = user_data.get(message.chat.id, {})
    # send_movie_by_pref(message.chat.id, prefs)
    page = random.randint(1, 50)
    rndm_url = f"https://api.themoviedb.org/3/movie/popular?api_key={tmdb}&language=ru-RU&page={page}"

    rndm_request = requests.get(rndm_url).json()
    films = rndm_request.get('results', [])
    if not films:
        bot.send_message(message.chat.id, 'Фильм не найден')
        return

    film = random.choice(films)

    title = film.get('title') or film.get('name')
    overview = film.get('overview', 'Описание отсутствует')
    rating = film.get('vote_average', 'Рейтинг отсутствует')
    poster = film.get('poster_path')

    text = f'{title}\n\nРейтинг: {rating}\n\n{overview}'
    if poster:
        bot.send_photo(message.chat.id, f'https://image.tmdb.org/t/p/w500{poster}', caption=text, parse_mode='Markdown')
    else:
        bot.send_message(message.chat.id, text)


@bot.message_handler(commands=['actor_films'])
def actor_films(message):
    prefs = user_data.get(message.chat.id)
    if not prefs or not prefs.get('actor'):
        bot.send_message(message.chat.id,"Ты не указал актера в опроснике. Напиши его имя через /start")
        bot.register_next_step_handler(message,actor_films_search)
    else:
        actor_films_search(message, actor_name=prefs['actor'])

def actor_films_search(message, actor_name=None):
    if not actor_name:
        actor_name = message.text
    url_actor = f"https://api.themoviedb.org/3/search/person?api_key={tmdb}&language=ru-RU&query={actor_name}"
    data_actor = requests.get(url_actor).json()
    if not data_actor['results']:
        bot.send_message(message.chat.id,"Актер не найден")
        return
    actor_id = data_actor['results'][0]['id']
    url_films = f"https://api.themoviedb.org/3/person/{actor_id}/movie_credits?api_key={tmdb}&language=ru-RU"
    films = requests.get(url_films).json().get("cast",[])
    if not films:
        bot.send_message(message.chat.id,"Фильмы с этим актером не найдены")
        return
    top_films = sorted(films, key=lambda film: film.get('vote_average', 0), reverse=True)[:5]
    for film in top_films:
        send_film(message.chat.id,film)

@bot.message_handler(commands=['genres'])
def genres(message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True,row_width=2)
    keyboard.add("Боевик","Комедия","Романтика","Фантастика")
    bot.send_message(message.chat.id,"Выбери жанр фильма")
    bot.register_next_step_handler(message,sel_genre)

def sel_genre(message):
    genre = message.text
    user_data[message.chat.id]["genre"] = genre

    actor = user_data[message.chat.id].get('actor')
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True,row_width=2)
    keyboard.add("2025","2024","Любой","2023")
    bot.send_message(message.chat.id,"Выберите год")
    bot.register_next_step_handler(message, lambda message: send_genre_films(message, genre, actor))

def send_genre_films(message, genre, actor):
    year = message.text
    genres = {"Боевик":"28", "Комедия":"35", "Романтика":"10749", "Фантастика":"878"}
    genre_id = genres.get(genre)
    url = f"https://api.themoviedb.org/3/discover/movie?api_key={tmdb}&with_genres={genre_id}&language=ru-RU"

    if actor:
        data_actor = requests.get(f"https://api.themoviedb.org/3/search/person?api_key={tmdb}&language=ru-RU&query={actor}").json()
        if data_actor['results']:
            actor_id = data_actor['results'][0]['id']
            url += f"&with_cast={actor_id}"

    if year != "Любой":
        url += f"&primary_release_year={year}"

    films = requests.get(url).json().get('results',[])
    if not films:
        bot.send_message(message.chat.id,"Фильмы не найдены",reply_markup=types.ReplyKeyboardRemove())
        return

    film = random.choice(films)
    send_film(message.chat.id,film)


@bot.message_handler(commands=['trailer'])
def trailer(message):
    bot.send_message(message.chat.id,"Напиши название фильма и я пришлю тебе трейлер")
    bot.register_next_step_handler(message,get_trailer)

def get_trailer(message):
    name = message.text
    url_search = f"https://api.themoviedb.org/3/search/movie?api_key={tmdb}&language=ru-RU&query={name}"
    data = requests.get(url_search).json()
    if not data['results']:
        bot.send_message(message.chat.id,"Фильм не найден")
        return
    film_id = data['results'][0]['id']
    url_trailer = f"https://api.themoviedb.org/3/movie/{film_id}/videos?api_key={tmdb}&language=ru-RU"
    videos = requests.get(url_trailer).json().get('results',[])
    trailer = next((v for v in videos if v["type"]=="Trailer" and v["site"]=="YouTube"), None)
    if not trailer:
        bot.send_message(message.chat.id,"Трейлкер не найден")
        return
    yt_url = f"https://www.youtube.com/watch?v={trailer['key']}"
    bot.send_message(message.chat.id,f"Вот трейлер:\n{yt_url}")


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



def send_film(chat_id, film):
    title = film.get("title") or film.get("name")
    overview = film.get("overview","Описание отсутствует")
    rating = round(film.get('vote_average',0))
    poster = film.get('poster_path')
    text = f"{title}\nРейтинг:{rating}\n\n{overview}"
    if poster:
        bot.send_photo(chat_id,f"https://image.tmdb.org/t/p/w500{poster}",caption=text)
    else:
        bot.send_message(chat_id,text)


def send_movie_by_pref(chat_id, prefs):
    genres = {"Боевик":"28", "Комедия":"35", "Романтика":"10749", "Фантастика":"878"}
    genre_id = genres.get(prefs.get('genre'))
    url = f"https://api.themoviedb.org/3/discover/movie?api_key={tmdb}&language=ru-RU"
    if genre_id:
        url += f"&with_genres={genre_id}"
    if prefs.get("actor"):
        data_actor = requests.get(f"https://api.themoviedb.org/3/search/person?api_key={tmdb}&language=ru-RU&query={prefs['actor']}").json()
        if data_actor["results"]:
            actor_id = data_actor['results'][0]['id']
            url += f"&with_cast={actor_id}"
    if prefs.get("new") == "Новый":
        url += f"&sort_by=release_date.desc"


    films = requests.get(url).json().get("results",[])
    if not films:
        bot.send_message(chat_id,"Фильмы не найдены")
        return

    if prefs.get("rating") == "Топовый":
        film = max(films, key=lambda x: x.get("vote_average",0))
    else:
        film = random.choice(films)
    send_film(chat_id, film)


bot.polling(none_stop=True)
