import telebot
from telebot import types 
import requests
import json

recipes_cache = {}

def load_settings():
    with open("settings.json", "r", encoding="utf-8") as f:
        return json.load(f)

def save_settings(data):
    with open("settings.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)  

bot = telebot.TeleBot('8485418451:AAEVmkbR1HwmTu2yzK6oWsuW5qiC7k3xV3s')
API_KEY = ("a2a421e9c0474124b73fd674e30c0d85")

@bot.message_handler(commands=['start'])
def main(message):
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton('Составить меню на неделю', callback_data='menu')
    markup.row(btn1) 
    btn2 = types.InlineKeyboardButton('Настройки диеты', callback_data='setting')
    btn3 = types.InlineKeyboardButton('Продукты и цены', callback_data='prices')
    markup.row(btn2, btn3) 
    btn4 = types.InlineKeyboardButton('💙 Избранное', callback_data='show_fav')
    markup.row(btn4) 

    
    bot.send_message(
        message.chat.id,
        f'Привет, {message.from_user.first_name}. Я бот-планирования питания! Давай вместе составим меню на неделю.',
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda c: True)
def callback_message(callback):
    data = callback.data
    chat_id = callback.message.chat.id

    if data == "menu":
        show_menu_options(callback)

    elif data == "setting":
        show_settings(callback)

    elif data == "prices":
        bot.send_message(chat_id, "Цены продуктов скоро добавлю!")

    elif data in ["without_beef", "without_fish", "without_milk", "without_sugar", "all"]:
        choose_goal(callback)

    elif data in ["deficit", "proficit", "normall"]:
        bot.send_message(chat_id, f"Отлично! Ты выбрал цель: {data}. Можно генерировать меню!")
        user_state[chat_id] = "enter_product"
        bot.send_message(chat_id, "Напиши продукт на английском, по которому искать рецепты:")

    elif data.startswith("fav|"):
        recipe_id = data.split("|")[1]
        recipe = recipes_cache.get(recipe_id)
        if recipe:
            add_to_favorites(chat_id, recipe["title"], recipe["url"])

    elif data == "show_fav":
        show_favorites(callback)

    elif data.startswith("remove_fav|"):
        index = int(data.split("|")[1])
        chat_id_str = str(chat_id)
        data_settings = load_settings()
        favorites = data_settings["favorites"].get(chat_id_str, [])

        if 0 <= index < len(favorites):
            removed_recipe = favorites.pop(index)
            save_settings(data_settings)
            bot.send_message(chat_id, f"❌ Удалено из избранного: {removed_recipe['title']}")
        else:
            bot.send_message(chat_id, "Ошибка при удалении.")

    elif data == "add_exclusion":
        user_state[chat_id] = "add"
        bot.send_message(chat_id, "Напиши продукт на английском, который хочешь исключить:")

    elif data == "remove_exclusion":
        user_state[chat_id] = "remove"
        bot.send_message(chat_id, "Какие продукты ты хочешь удалить из исключений?")

    elif data == "list_exclusion":
        show_exclusion(callback)


def show_menu_options(callback):
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton('Без говядины 🥩', callback_data='without_beef')
    btn2 = types.InlineKeyboardButton('Без рыбы 🐟', callback_data='without_fish')
    markup.row(btn1, btn2) 
    btn3 = types.InlineKeyboardButton('Без молочки 🥛', callback_data='without_milk')
    btn4 = types.InlineKeyboardButton('Без сахара 🍭', callback_data='without_sugar')
    markup.row(btn4, btn3) 
    btn5 = types.InlineKeyboardButton('Все можно ✅', callback_data='all')
    markup.row(btn5) 


    bot.send_message(
        callback.message.chat.id,
        "Выбери свои ограничения:",
        reply_markup=markup
    )


def choose_goal(callback):
    restriction = callback.data
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton('Дефицит', callback_data='deficit')
    btn2 = types.InlineKeyboardButton('Профицит', callback_data='proficit')
    markup.row(btn1, btn2) 
    btn3 = types.InlineKeyboardButton('Поддержание', callback_data='normall')
    markup.row(btn3) 
    bot.send_message(callback.message.chat.id, "Какая у тебя цель?", reply_markup=markup)


def show_settings(callback):
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton('Напиши исключения ', callback_data='add_exclusion')
    btn2 = types.InlineKeyboardButton('Убрать исключения', callback_data='remove_exclusion')
    markup.row(btn1, btn2) 
    btn3 = types.InlineKeyboardButton('Список исключений', callback_data='list_exclusion') 
    markup.row(btn3) 

    bot.send_message(
        callback.message.chat.id,
        "Настройки диеты:",
        reply_markup=markup
    )
  
def show_exclusion(callback):
    data = load_settings()
    exclusion = data["exclusion"]

    if len(exclusion) == 0:
        text = "У тебя нет исключений."
    else:
        text = "Твои исключения:\n" + "\n".join("• " + r for r in exclusion)

    bot.send_message(callback.message.chat.id, text)



user_state= {}

@bot.message_handler(func=lambda m: user_state.get(m.chat.id) == "add")
def add_exclusion_text(message):
    text = message.text.lower()

    data = load_settings()
    if text in data["exclusion"]:
     bot.send_message(message.chat.id, "Это уже есть в списке исключений")
    else:
     data["exclusion"].append(text)
    save_settings(data)
    bot.send_message(message.chat.id, f"Добавил '{text}' в исключения!")

    user_state[message.chat.id] = None



@bot.message_handler(func=lambda m: user_state.get(m.chat.id) == "remove")
def remove_exclusion_text(message):
    text = message.text.lower()
    
    data = load_settings()
    if text in data["exclusion"]:
        data["exclusion"].remove(text)
        save_settings(data)
        bot.send_message(message.chat.id, f"Удалил '{text}' из исключений!")
    else:
        bot.send_message(message.chat.id, f"'{text}' нет в списке исключений.")
    
    user_state[message.chat.id] = None




def get_recipes(query):
    url = f"https://api.spoonacular.com/recipes/complexSearch?query={query}&number=5&apiKey={API_KEY}"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        recipes = []
        for r in data.get("results", []):
            recipe_info = {
                "title": r.get("title"),
                "url": f"https://spoonacular.com/recipes/{r.get('title').replace(' ', '-')}-{r.get('id')}",
                "image": r.get("image")
            }
            recipes.append(recipe_info)
        return recipes
    else:
        return None

@bot.message_handler(func=lambda m: user_state.get(m.chat.id) == "enter_product")
def handle_product(message):
    query = message.text.lower()
    recipes = get_recipes(query)

    if not recipes:
        bot.send_message(message.chat.id, "Ничего не найдено 😔")
        user_state[message.chat.id] = None
        return

    for r in recipes:
        recipe_id = str(len(recipes_cache) + 1)
        recipes_cache[recipe_id] = r

        markup = types.InlineKeyboardMarkup()
        fav_btn = types.InlineKeyboardButton(
            "💙В избранное",
            callback_data=f"fav|{recipe_id}"
        )
        markup.add(fav_btn)

        bot.send_message(
            message.chat.id,
            f"🍽 {r['title']}\n{r['url']}",
            reply_markup=markup
        )

    user_state[message.chat.id] = None


def add_to_favorites(chat_id, title, url):
    data = load_settings()
    favorites = data["favorites"]

    chat_id_str = str(chat_id)

    if chat_id_str not in favorites:
        favorites[chat_id_str] = []

    favorites[chat_id_str].append({
        "title": title,
        "url": url
    })

    save_settings(data)

    markup = types.InlineKeyboardMarkup()
    fav_btn = types.InlineKeyboardButton(
        "💙 Избранное",
        callback_data="show_fav"
    )
    markup.add(fav_btn)

    bot.send_message(chat_id, "Рецепт добавлен в избранное!", reply_markup=markup)

def remove_from_favorites(chat_id, title):
    data = load_settings()
    chat_id = str(chat_id)

    if chat_id in data["favorites"]:
        data["favorites"][chat_id] = [
            r for r in data["favorites"][chat_id]
            if r["title"] != title
        ]


def show_favorites(callback):
    data = load_settings()
    chat_id = str(callback.message.chat.id)

    favorites = data["favorites"].get(chat_id, [])

    if not favorites:
        bot.send_message(callback.message.chat.id, "У тебя пока нет избранных рецептов.")
        return
    for index, r in enumerate(favorites):
        markup = types.InlineKeyboardMarkup()
        remove_btn = types.InlineKeyboardButton(
            "❌ Удалить",
            callback_data=f"remove_fav|{index}"
        )
        markup.add(remove_btn)
        bot.send_message(
            callback.message.chat.id,
            f"💙 {r['title']}\n{r['url']}",
            reply_markup=markup
        )

    save_settings(data)







bot.polling(skip_pending=True)
