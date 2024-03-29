from Vkinder import *
from keyboard import keyboard3


for event in bot.longpoll.listen():
    if event.type == VkEventType.MESSAGE_NEW and event.to_me:
        message_text = event.text.lower()
        user_id = str(event.user_id)

        if message_text == 'нажми, чтобы узнать что я умею \N{smiling face with sunglasses}':
            bot.write_msg(user_id,
                          f'Приветствую, {bot.name(user_id)}! Я - чат-бот VKinder, и я помогу Вам найти пару. Для '
                          f'этого я буду использовать следующие критерии: возраст, пол, город, семейное положение. Я '
                          f'отправлю Вам топ-3 самых популярных фото профиля, сквозь которые Вы сможете составить '
                          f'первое впечатление о возможном партнере. Можно воспользоваться как автоматическим поиском '
                          f'так и поиском по индивидуальным параметрам. Если не понравится жми "Еще варианты", '
                          f'у меня в запасе их много!\n'
                          f'\n Чтобы удалить историю просмотра нажми "Удалить историю"', keyboard=keyboard3)

        elif message_text == 'удалить историю':
            reset_profile_loading_counter(user_id)
            drop_seen_users(user_id)
            bot.write_msg(user_id, f'Хорошо, {bot.name(user_id)} ваша история удалена!')

        elif message_text == 'начать автоматический поиск':
            create_table_seen_users(engine)
            bot.write_msg(user_id, f'Хорошо, {bot.name(user_id)} приступим')
            bot.send_info_about_users(user_id)

        elif message_text == 'начать поиск по заданным параметрам':
            create_table_seen_users(engine)
            bot.write_msg(user_id, f'Хорошо, {bot.name(user_id)} приступим')
            bot.send_info_about_users_individual_parameters(user_id)

        else:
            bot.write_msg(event.user_id, 'Я не понимаю вас, повторите запрос')
