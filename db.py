
def create_tables(conn):
    with conn.cursor() as cursor:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users(
        id SERIAL PRIMARY KEY,
        vk_id INTEGER NOT NULL UNIQUE,
        first_name VARCHAR(30) NOT NULL,
        last_name VARCHAR(30) NOT NULL,     
        age INTEGER NOT NULL,
        city_id INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS result_users(
        id SERIAL PRIMARY KEY,
        vk_id INTEGER NOT NULL UNIQUE,
        user_id INT REFERENCES users(id) ON DELETE CASCADE
        );
        """)
        conn.commit()
        print('Таблицы успешно созданы.')


def delete_tables(conn):
    with conn.cursor() as cursor:
        cursor.execute("""
        DROP TABLE IF EXISTS users CASCADE;
        DROP TABLE IF EXISTS result_users;
        DROP TABLE IF EXISTS find_user CASCADE;
        DROP TABLE IF EXISTS find_user_photo;
        """)
        conn.commit()
        print('Таблицы успешно удалены.')


def insert_user(conn, user_info):
    print(user_info)
    with conn.cursor() as cursor:
        cursor.execute("""
        INSERT INTO users(vk_id, first_name, last_name, age, city_id) VALUES
        (%s, %s, %s, %s, %s) RETURNING id
        """, (user_info.get('id'),
              user_info.get('first_name'),
              user_info.get('last_name'),
              user_info.get('age'),
              user_info.get('city'),))
        user_db_id = cursor.fetchone()[0]
    conn.commit()
    if user_db_id:
        return user_db_id
    else:
        return False


def insert_result_user(conn, user_db_id, finally_selected_user):
    print(user_db_id)
    with conn.cursor() as cursor:
        cursor.execute("""
        INSERT INTO result_users(vk_id, user_id) VALUES
        (%s, %s) RETURNING id
        """, (finally_selected_user.get('id'),
              user_db_id,))
    conn.commit()


def get_user_db_id(conn, vk_id):
    with conn.cursor() as cursor:
        cursor.execute("""
        SELECT id FROM users
        WHERE vk_id = %s
        """, (vk_id,))
        user_db_id = cursor.fetchone()
    if user_db_id:
        return user_db_id[0]
    else:
        return False


def check_result_user(conn, user_id):
    with conn.cursor() as cursor:
        cursor.execute("""
        SELECT vk_id FROM result_users
        WHERE vk_id = %s
        """, (user_id,))
        user_db_id = cursor.fetchone()
    if user_db_id is not None:
        return False
    else:
        return True
