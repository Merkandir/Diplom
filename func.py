import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType

import datetime
import time
from random import randint

from db import *


# with open('group_token.txt', 'r') as f:
#     bot_token = f.readline().strip()
#
# with open('user_token.txt', 'r') as f:
#     user_token = f.readline().strip()

bot_token = input('Введите токен бота группы с необходимыми правами: ')
user_token = input('Введите токен приложения с необходимыми правами: ')

vk_bot_token = vk_api.VkApi(token=bot_token)
vk_app_token = vk_api.VkApi(token=user_token)
long_poll = VkLongPoll(vk_bot_token)


def write_msg(user_id, message):
    vk_bot_token.method('messages.send', {'user_id': user_id, 'message': message, 'random_id': 0, })


def write_photo_msg(user_id, message, selected_user, photo_list):
    attachment = ''
    for photo_id in photo_list:
        attachment += f"photo{selected_user['id']}_{photo_id},"

    vk_bot_token.method('messages.send', {'user_id': user_id, 'message': message, "attachment": attachment,
                                          'random_id': 0, })


def get_city(city):
    values = {
        'country_id': 1,
        'q': city,
        'count': 1
    }
    response = vk_app_token.method('database.getCities', values=values)
    if response['items']:
        if len(response['items'][0]['title']) != city:
            print(response['items'][0]['title'])

        city_id = response['items'][0]['id']
        return city_id
    else:
        return False


def bdate_to_age(bdate):
    age = datetime.datetime.now().year - int(bdate[-4:])
    return age


def get_user_info(user_id):
    user_info_dict = {}
    response = vk_bot_token.method('users.get', {'user_id': user_id,
                                                 'v': 5.131,
                                                 'fields': 'first_name, last_name, bdate, sex, city'})

    if response:
        for key, values in response[0].items():
            if key == 'is_closed' or key == 'can_access_closed':
                break
            elif key == 'city':
                user_info_dict[key] = values['id']
            else:
                user_info_dict[key] = values
    return user_info_dict


def get_additional_information(user_info):
    user_info = user_info
    for event in long_poll.listen():
        if 'bdate' not in user_info or user_info['bdate'].split('.') != 3:
            if 'bdate' in user_info:
                user_info.pop('bdate')
            write_msg(event.user_id, "Введите ваш возраст (только цифры):")
            for event in long_poll.listen():
                if event.type == VkEventType.MESSAGE_NEW:
                    if event.to_me:
                        request_age = event.text.lower().strip()
                        try:
                            user_info['age'] = int(request_age)
                            if user_info['age'] < 18:
                                write_msg(event.user_id, "Сервис недоступен для пользователей моложе 18 лет! &#128286;")
                                return
                            break
                        except Exception as _ex:
                            print(_ex)
                            write_msg(event.user_id, "Неверный формат возраста, "
                                                     "вводите только цифры:")
                            continue

        if 'city' not in user_info:
            write_msg(event.user_id, "Введите ваш город:")
            for event in long_poll.listen():
                if event.type == VkEventType.MESSAGE_NEW:
                    if event.to_me:
                        request_city = event.text.lower().strip()
                        if get_city(request_city):
                            user_info['city'] = get_city(request_city)
                            break
                        else:
                            write_msg(event.user_id, 'Неверно указан город! Введите правильное полное название:')
                            continue

        return user_info


def find_users(user_info):
    if (user_info['age'] - 3) < 18:
        find_age = 18
    else:
        find_age = user_info['age'] - 3
    user_list = []
    while find_age <= user_info['age'] + 3:
        response = vk_app_token.method('users.search', {
                                        'age_from': find_age,
                                        'age_to': find_age,
                                        'sex': 3 - user_info['sex'],
                                        'city': user_info['city'],
                                        'status': 6,
                                        'has_photo': 1,
                                        'count': 1000,
                                        'v': 5.131})

        if response:
            if response.get('count') != 0:
                if response.get('items'):
                    for items in response.get('items'):
                        if items['is_closed']:
                            continue
                        else:
                            user_list.append(items)
                    find_age += 1
                    time.sleep(1)
            else:
                return False
        else:
            return False
        if find_age == user_info['age'] + 3:
            return len(user_list), user_list
    return False


def get_random_user(users_list_range, users_list):
    selected_user = users_list[randint(1, users_list_range)]
    return selected_user


def get_photos(selected_user):
    response = vk_app_token.method('photos.get', {'owner_id': selected_user['id'],
                                                  'album_id': f'profile',
                                                  'photo_sizes': 1,
                                                  'count': 1000,
                                                  'extended': 1})
    if response:
        return response
    else:
        return False


def get_final_selection(conn, users_list_range, users_list):
    while True:
        selected_user = get_random_user(users_list_range, users_list)
        photos_info = get_photos(selected_user)
        if photos_info.get('count') < 3:
            continue
        if check_result_user(conn, selected_user.get('id')):
            return selected_user, photos_info
        else:
            continue


def get_most_popular_photo(photos_info):
    photo_info_dict = {}
    link_id_list = []
    for items in photos_info.get('items'):
        key = items.get('id')
        photo_info_dict[key] = items.get('likes').get('count') + items.get('comments').get('count')
    photo_info_dict = sorted(photo_info_dict.items(), key=lambda x: x[1], reverse=True)[:3]
    for key, values in photo_info_dict:
        link_id_list.append(key)
    return link_id_list
