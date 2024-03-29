import datetime
from random import randrange

import requests
import vk_api
from vk_api.longpoll import VkEventType, VkLongPoll

from config import user_token, comm_token
from database import *
from keyboard import keyboard1, keyboard2, main_keyboard
from method import Data

dictionary = {}


def profile_loading_counter(user_id):
    user_id = int(user_id)
    if user_id in dictionary:
        dictionary[user_id] += 20
    else:
        dictionary[user_id] = 20
    return dictionary[user_id]


def reset_profile_loading_counter(user_id):
    try:
        user_id = int(user_id)
        dictionary.pop(user_id)
    except KeyError:
        pass


class VKBotSearch:
    def __init__(self):
        print('Бот запущен')
        self.vk = vk_api.VkApi(token=comm_token)
        self.longpoll = VkLongPoll(self.vk)
        self.data = Data()

    def loop_bot(self):
        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                message_text = event.text
                return message_text, event.user_id

    def write_msg(self, user_id, message, keyboard=main_keyboard, attachment=None):
        """SendMessage"""
        self.vk.method('messages.send', {'user_id': user_id,
                                         'message': message,
                                         'random_id': randrange(10 ** 7),
                                         'attachment': attachment,
                                         'keyboard': keyboard
                                         })

    def name(self, user_id):
        """Функция получения имени пользователя"""
        first_name = self.data.get_info_user(user_id)['first_name']
        return first_name

    def get_sex(self, user_id):
        """Функция получения пола пользователя для автоматического подбора"""
        sex = self.data.get_info_user(user_id)['sex']
        if sex == 2:
            sex = 1
            return sex
        elif sex == 1:
            sex = 2
            return sex

    def get_sex_individual_parameters(self, user_id):
        """Функция получения пола для поиска по индивидуальным параметрам"""
        self.write_msg(user_id, 'Введите пол для поиска (мужской/женский): ')
        msg_text, user_id = self.loop_bot()
        if msg_text == 'мужской':
            msg_text = 2
            return msg_text
        elif msg_text == 'женский':
            msg_text = 1
            return msg_text
        else:
            self.write_msg(user_id, 'Некорректный ввод')
            return self.get_sex_individual_parameters(user_id)

    def get_age(self, user_id):
        """Функция получения возраста для автоматического подбора"""
        bdate = self.data.get_info_user(user_id)['bdate'].split('.')
        if len(bdate) == 3:
            age = int(datetime.date.today().year) - int(bdate[2])
            age_from = str(age - 1)
            age_to = str(age + 1)
        elif len(bdate) == 2:
            age_from = self.get_age_low(user_id)
            age_to = self.get_age_high(user_id)
        else:
            return None

        return age_from, age_to

    def get_age_low(self, user_id):
        """Функция получения возраста по нижней границе для индивидуального подбора"""
        self.write_msg(user_id, 'Введите минимальный порог возраста (min - 18): ')
        msg_text, user_id = self.loop_bot()
        age_from = int(msg_text)
        if age_from < 18:
            self.write_msg(user_id, 'Некорректный ввод')
            return self.get_age_low(user_id)
        else:
            return age_from

    def get_age_high(self, user_id):
        """Функция получения возраста по верхней границе для индивидуального подбора"""
        self.write_msg(user_id, 'Введите верхний порог возраста (max - 99): ')
        msg_text, user_id = self.loop_bot()
        age_to = int(msg_text)
        if age_to > 99:
            self.write_msg(user_id, 'Некорректный ввод')
            return self.get_age_high(user_id)
        else:
            return age_to

    def find_city(self, user_id):
        """Функция получения информации о городе"""
        if 'city' not in self.data.get_info_user(user_id):
            return self.find_city_individual_parameters(user_id)
        else:
            hometown = self.data.get_info_user(user_id)['city']['title']
            return hometown

    def find_city_individual_parameters(self, user_id):
        """Функция получения города для индивидуального подбора"""
        self.write_msg(user_id, 'Введите название города для поиска: ')
        msg_text, user_id = self.loop_bot()
        hometown = str(msg_text)
        cities = self.data.get_cities(user_id)
        for city in cities:
            if city['title'] == hometown.title():
                self.write_msg(user_id, f'Ищу в городе {hometown.title()}')
                return hometown.title()

        self.write_msg(user_id, 'Некорректный ввод')
        self.find_city_individual_parameters(user_id)

    def find_user_params(self, user_id):
        """Параметры для автоматического поиска"""
        fields = 'id, sex, bdate, city, relation'
        age_from, age_to = self.get_age(user_id)
        params = {'access_token': user_token,
                  'v': '5.131',
                  'sex': self.get_sex(user_id),
                  'age_from': age_from,
                  'age_to': age_to,
                  'country_id': '1',
                  'hometown': self.find_city(user_id),
                  'fields': fields,
                  'status': '1' or '6',
                  'count': profile_loading_counter(user_id),
                  'has_photo': '1',
                  'is_closed': False
                  }
        return params

    def find_user_individual_parameters(self, user_id):
        """Параметры для поиска по заданным параметрам"""
        fields = 'id, sex, bdate, city, relation'
        params = {'access_token': user_token,
                  'v': '5.131',
                  'sex': self.get_sex_individual_parameters(user_id),
                  'age_from': self.get_age_low(user_id),
                  'age_to': self.get_age_high(user_id),
                  'country_id': '1',
                  'hometown': self.find_city_individual_parameters(user_id),
                  'fields': fields,
                  'status': '1' or '6',
                  'count': profile_loading_counter(user_id),
                  'has_photo': '1',
                  'is_closed': False
                  }
        return params

    def search_users(self, user_id):
        """Поиск людей по полученным данным для автоматического поиска"""
        method = 'users.search'
        all_persons = []
        url = f'https://api.vk.com/method/{method}'
        res = requests.get(url, self.find_user_params(user_id)).json()
        user_url = f'https://vk.com/id'
        count = res['response']['count']  # считаем сколько всего найдено анкет
        count_list = []  # считаем сколько анкет с открытым профилем и хотя бы одной фотографией
        for element in res['response'].get('items'):

            profile_pics = self.data.get_photos_id(element['id'])
            if profile_pics:
                attach = ''
                for pic in profile_pics['pics_ids']:
                    attach += f'photo{profile_pics["owner_id"]}_{pic},'
                person = [
                    element['first_name'],
                    element['last_name'],
                    user_url + str(element['id']),
                    element['id'],
                    attach
                ]
                all_persons.append(person)
                count_list = len(all_persons)
        print(
            f'Поиск пользователей закончен,всего найдено {count} пользователей. Загружаю для просмотра {count_list} пользователей')
        if count == 0:
            self.write_msg(user_id, f"К сожалению нет подходящих кандидатов")
            print('Нет подходящих кандидатов')
        else:
            self.write_msg(user_id,
                           f'Нашел для Вас несколько вариантов, проверяю есть ли фотографии и открыт ли профиль...')
        return all_persons

    def search_users_individual_parameters(self, user_id):
        """Поиск людей по полученным данным для поиска по заданным параметрам"""
        method = 'users.search'
        all_persons = []
        url = f'https://api.vk.com/method/{method}'
        res = requests.get(url, self.find_user_individual_parameters(user_id)).json()
        user_url = f'https://vk.com/id'
        count = res['response']['count']  # считаем сколько всего найдено анкет
        count_list = []  # считаем сколько анкет с открытым профилем и хотя бы одной фотографией
        for element in res['response'].get('items'):
            profile_pics = self.data.get_photos_id(element['id'])
            if profile_pics:
                attach = ''
                for pic in profile_pics['pics_ids']:
                    attach += f'photo{profile_pics["owner_id"]}_{pic},'
                person = [
                    element['first_name'],
                    element['last_name'],
                    user_url + str(element['id']),
                    element['id'],
                    attach
                ]
                all_persons.append(person)
                count_list = int(len(all_persons))
        print(
            f'Поиск пользователей закончен,всего найдено {count} пользователей. Загружаю для просмотра {count_list} пользователей')
        if count == 0:
            self.write_msg(user_id, f"К сожалению нет подходящих кандидатов")
            print('Нет подходящих кандидатов')
        else:
            self.write_msg(user_id,
                           f'Нашел для Вас несколько вариантов, проверяю есть ли фотографии и открыт ли профиль...')
        return all_persons

    def sorted_users(self, user_id):
        """Подготовка отсортированного списка профилей к просмотру"""
        profiles = self.search_users(user_id)
        profiles_to_send = []
        while len(profiles) > 0:
            profile = profiles.pop()
            if select(user_id, profile[3]) is None:  # проверяем нет ли найденного профиля в таблице просмотренных
                profiles_to_send.append(profile)
        return profiles_to_send

    def send_info_about_users(self, user_id):
        """Отправка информации пользователю"""
        profiles_to_send = self.sorted_users(user_id)
        if not profiles_to_send:
            self.write_msg(user_id, f'Все анкеты просмотрены')
        else:
            while len(profiles_to_send) > 0:
                profile = profiles_to_send.pop()
                insert_data_seen_users(user_id, profile[3])
                self.write_msg(user_id, f'\n{profile[0]}  {profile[1]}  {profile[2]}', attachment={profile[4]})
                self.write_msg(user_id, f'Посмотрите, как Вам этот кандидат? Не нравится, жми "Еще варианты!"',
                               keyboard=keyboard1)
                self.write_msg(user_id,
                               f'Чтобы начать новый поиск, или просмотреть, что я умею нажми "Закончить просмотр"',
                               keyboard=keyboard2)
                msg_text, user_id = self.loop_bot()
                if msg_text == 'Еще варианты':
                    continue
                else:
                    self.write_msg(user_id, f'Жду дальнейших распоряжений!')
                    break
            else:
                self.send_info_about_users(user_id)

    def sorted_users_individual_parameters(self, user_id):
        """Подготовка отсортированного списка профилей к просмотру"""
        profiles = self.search_users_individual_parameters(user_id)
        profiles_to_send = []
        while len(profiles) > 0:
            profile = profiles.pop()
            if select(user_id, profile[3]) is None:
                profiles_to_send.append(profile)
        return profiles_to_send

    def send_info_about_users_individual_parameters(self, user_id):
        """Отправка информации пользователю"""
        profiles_to_send = self.sorted_users_individual_parameters(user_id)
        if not profiles_to_send:
            self.write_msg(user_id, f'Все анкеты просмотрены')
        else:
            while len(profiles_to_send) > 0:
                profile = profiles_to_send.pop()
                insert_data_seen_users(user_id, profile[3])
                self.write_msg(user_id, f'\n{profile[0]}  {profile[1]}  {profile[2]}', attachment={profile[4]})
                self.write_msg(user_id, f'Посмотрите, как Вам этот кандидат? Не нравится, жми "Еще варианты!"',
                               keyboard=keyboard1)
                self.write_msg(user_id,
                               f'Чтобы начать новый поиск, или просмотреть, что я умею нажми "Закончить просмотр"',
                               keyboard=keyboard2)
                msg_text, user_id = self.loop_bot()
                if msg_text == 'Еще варианты':
                    continue
                else:
                    self.write_msg(user_id, f'Жду дальнейших распоряжений!')
                    break
            else:
                self.send_info_about_users_individual_parameters(user_id)


bot = VKBotSearch()
