from func import *
import psycopg2


def main():
    for event in long_poll.listen():
        if event.type == VkEventType.MESSAGE_NEW:
            if event.to_me:
                request = event.text.lower().strip()
                if request == "привет":
                    user_info = get_user_info(event.user_id)
                    write_msg(event.user_id, f"Привет, {user_info.get('first_name')}!")
                elif request == "пока":
                    write_msg(event.user_id, "Пока((")
                elif request == "го":
                    conn = psycopg2.connect(database="vkdb", user="postgres", password="123")
                    user_info = get_user_info(event.user_id)
                    if user_info:

                        if len(user_info) != 6 or len(user_info['bdate'].split('.')) != 3:
                            write_msg(event.user_id, "Недостаточно информации, пожалуйста, заполните пробелы &#128373;")
                            user_info = get_additional_information(user_info)
                        else:
                            user_age = bdate_to_age(user_info['bdate'])
                            if user_age < 18:
                                write_msg(event.user_id,
                                          "Сервис недоступен для пользователей моложе 18 лет! &#128286;")
                                continue
                            else:
                                user_info['age'] = user_age
                                if 'bdate' in user_info:
                                    user_info.pop('bdate')

                        if user_info:
                            try:
                                user_db_id = insert_user(conn, user_info)
                            except psycopg2.errors.UniqueViolation:
                                conn.rollback()
                                user_db_id = get_user_db_id(conn, str(user_info['id']))
                            except Exception as _ex:
                                user_db_id = False
                                print(_ex)
                                pass

                            if user_db_id:
                                write_msg(event.user_id, "Отлично, ищем пару! Это займёт некоторое время... &#129300;")

                                try:
                                    find_users_range, find_users_list = find_users(user_info)
                                    write_msg(event.user_id,
                                              f"По вашим данным найдено {find_users_range} "
                                              f"результатов, выбираем тот самый профиль...&#128522;")

                                    finally_selected_user, photos_info = get_final_selection(conn,
                                                                                             find_users_range,
                                                                                             find_users_list,
                                                                                             user_db_id)

                                    try:
                                        insert_result_user(conn, user_db_id, finally_selected_user)
                                    except Exception as _ex:
                                        print(_ex)

                                    photos_link = get_most_popular_photo(photos_info)
                                    write_photo_msg(event.user_id,
                                                    f"""Вам подходит {finally_selected_user.get('first_name')}"""
                                                    f"""{finally_selected_user.get('last_name')} &#128150;\n"""
                                                    f"""Профиль: https://vk.com/id{finally_selected_user.get('id')}\n"""
                                                    f"""Самые популярные фоторафии:""", finally_selected_user,
                                                    photos_link)
                                except Exception as _ex:
                                    print(_ex)
                                    write_msg(event.user_id,
                                              f"К сожалению нет людей в вашем городе, подходящих под ваши параметры,"
                                              f"попробуйте выбрать ближайшие города.")

                    conn.close()

                else:
                    write_msg(event.user_id, "Не поняла вашего ответа...")


if __name__ == '__main__':
    # conn = psycopg2.connect(database="vkdb", user="postgres", password="123")
    # delete_tables(conn)
    # create_tables(conn)
    # conn.close()

    main()
