import requests
import psycopg2

BASE_URL = "http://localhost:5000"


def fill_table():
    # Подключение к базе данных
    conn = psycopg2.connect(
        host="localhost",
        port="5432",
        database="dbname",
        user="user",
        password="password"
    )

    # Создание курсора
    cur = conn.cursor()

    # # SQL-запрос на создание таблицы users
    # sql = """
    #     CREATE TABLE users (
    #         id SERIAL PRIMARY KEY,
    #         full_name VARCHAR(255) NOT NULL,
    #         email VARCHAR(255) UNIQUE NOT NULL,
    #         phone VARCHAR(255) UNIQUE NOT NULL,
    #         password VARCHAR(255) NOT NULL,
    #         created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    #         updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    #     )
    # """
    #
    # cur.execute(sql)
    # conn.commit()
    #
    # # SQL-запрос на создание таблицы products
    # sql = """
    #     CREATE TABLE products (
    #         id SERIAL PRIMARY KEY,
    #         name VARCHAR(255) NOT NULL,
    #         price INTEGER NOT NULL,
    #         is_active BOOLEAN NOT NULL DEFAULT true,
    #         created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    #         updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    #
    #     )
    # """
    #
    # cur.execute(sql)
    # conn.commit()

    cur.execute("SELECT COUNT(*) FROM products")

    result = cur.fetchone()

    if result[0] > 0:
        print("Таблица products не пуста")
    else:
        # SQL-запрос на заполнение таблицы products
        sql = """
            INSERT INTO products (name, price, is_active) VALUES
            ('Product 1', 10, true),
            ('Product 2', 20, true),
            ('Product 3', 30, true)
        """

        cur.execute(sql)
        conn.commit()


    # # SQL-запрос на создание таблицы carts
    # sql = """
    #     CREATE TABLE carts (
    #         id SERIAL PRIMARY KEY,
    #         user_id INTEGER REFERENCES users(id),
    #         created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    #         updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    #     )
    # """
    #
    # cur.execute(sql)
    # conn.commit()
    #
    # # SQL-запрос на создание таблицы cart_items
    # sql = """
    #     CREATE TABLE cart_items (
    #         id SERIAL PRIMARY KEY,
    #         cart_id INTEGER NOT NULL,
    #         product_id INTEGER NOT NULL,
    #         quantity INTEGER NOT NULL,
    #         FOREIGN KEY (cart_id) REFERENCES carts (id),
    #         FOREIGN KEY (product_id) REFERENCES products (id)
    #     )
    # """
    #
    # cur.execute(sql)
    # conn.commit()

    # Закрытие курсора и соединения
    cur.close()
    conn.close()


# Получение токена доступа
def get_access_token(email, password):
    url = f"{BASE_URL}/login"
    data = {
        "email_or_phone": email,
        "password": password,
    }
    response = requests.post(url, json=data)

    return response.json().get("access_token")


# Регистрация нового пользователя
def register_user(full_name, email, phone, password, password_confirmation):
    url = f"{BASE_URL}/register"
    data = {
        "full_name": full_name,
        "email": email,
        "phone": phone,
        "password": password,
        "password_confirmation": password_confirmation,
    }
    response = requests.post(url, json=data)

    return response.json()


# Авторизация пользователя
def login(email_or_phone, password):
    url = f"{BASE_URL}/login"
    data = {
        "email_or_phone": email_or_phone,
        "password": password,
    }
    headers = {
        'Authorization': 'Bearer ACCESS_TOKEN'
    }
    response = requests.post(url, json=data, headers=headers)

    return response.json()


# Получение списка товаров
def get_items(token):
    url = f"{BASE_URL}/items"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    return response.json()


# Получение списка товаров постранично
def get_items_by_page(token, page, per_page):
    url = f"{BASE_URL}/items_by_page/{page}/{per_page}"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    return response.json()


# Получение корзины пользователя
def get_cart(token):
    url = f"{BASE_URL}/cart"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    return response.json()


# Получение общей стоимости корзины
def total_cost(token):
    url = f"{BASE_URL}/cart"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    cart = response.json()
    return cart.get("total")


# Добавление одного товара в корзину
def add_to_cart(token, item_id, quantity):
    data = {"product_id": item_id, "quantity": quantity}
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{BASE_URL}/add_to_cart", json=data, headers=headers)
    return response.json()


# Добавление нескольких товаров в корзину
def add_multiple_to_cart(token):
    items = get_items(token)
    if "items" in items:
        items = items["items"]
    else:
        return items
    item_ids = [item.get("id") for item in items]
    data = [{"product_id": item_id, "quantity": 1} for item_id in item_ids]
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{BASE_URL}/add_to_cart", json=data, headers=headers)
    return response.json()


# Удаление товара из корзины
def remove_from_cart(token, item_id, quantity):
    response = requests.delete(f"{BASE_URL}/remove_from_cart/{item_id}/{quantity}", headers={"Authorization": f"Bearer {token}"})
    return response.json()


# Полная очистка корзины
def clear_cart(token):
    response = requests.delete(f"{BASE_URL}/clear_cart", headers={"Authorization": f"Bearer {token}"})
    return response.json()


# Тестирование
if __name__ == "__main__":

    fill_table()

    # Регистрация нового пользователя
    response = register_user("Test User8", "test8@example.com", "+79001262289", "r$egGGg32r32", "r$egGGg32r32")
    print("Register User Response:", response)

    # Авторизация пользователя
    response = login("test8@example.com", "r$egGGg32r32")
    print("Login Response:", response)

    if "access_token" in response:
        token = response["access_token"]
    else:
        token = None

    # Получение списка товаров
    response = get_items(token)
    print("Get Items Response:", response)

    response = get_items_by_page(token, 1, 1)
    print("Get Items by page:", response)

    response = get_cart(token)
    print("Cart:", response)

    response = add_to_cart(token, 1, 10)
    print("Add to cart:", response)

    response = total_cost(token)
    print("Total cost:", response)

    response = add_multiple_to_cart(token)
    print("Add multiple to cart:", response)

    response = remove_from_cart(token, 1, 0)
    print("Remove from cart:", response)

    response = remove_from_cart(token, 2, 1)
    print("Remove from cart:", response)

    response = clear_cart (token)
    print("Clear cart:", response)