from flask import Flask, request, jsonify
from models import db, User, Product, Cart, CartItem
import re

# Создание экземпляра Flask и подключение к базе данных
from utils import generate_access_token, decode_access_token

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://user:password@localhost:5432/dbname'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

Session = db.session

with app.app_context():
    db.create_all()


# Маршрут для создания нового пользователя
@app.route('/register', methods=['POST'])
def register_user():
    try:
        # Получаем данные из тела запроса
        data = request.get_json()

        # Проверяем наличие всех необходимых полей в запросе
        if 'full_name' not in data or 'email' not in data or 'phone' not in data or 'password' not in data or 'password_confirmation' not in data:
            raise ValueError('Missing required fields')

        # Проверяем, что пароль и подтверждение пароля совпадают
        if data.get('password_confirmation') != data['password']:
            raise ValueError('Password confirmation does not match')

        # Проверяем, что пароль длиннее 8 символов, содержит только латинские символы,
        # содержит хотя бы одну букву в верхнем регистре и хотя бы один символ из '$%&!:'
        password = data['password']
        if len(password) < 8 or not password.isascii() or not any(c.isupper() for c in password) or not any(c in '$%&!:' for c in password):
            raise ValueError('Password does not meet requirements')

        # Проверка написания email
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, data['email']):
            raise ValueError('Invalid email')

        # Проверяем телефон начинается с +7 после чего идут 10 цифр
        phone_regex = r'^\+7\d{10}$'
        if not re.match(phone_regex, data['phone']):
            raise ValueError('Invalid phone number')

        # Создаем новую запись пользователя
        new_user = User(full_name=data['full_name'], email=data['email'], phone=data['phone'], password=data['password'])

        session = Session()
        session.add(new_user)
        session.commit()

        # Возвращаем созданную запись в виде  JSON
        result = {'id': new_user.id, 'full_name': new_user.full_name, 'email': new_user.email, 'phone': new_user.phone, 'created_at': new_user.created_at}

        response = jsonify(result)

        session.close()

        return response

    except (ValueError, TypeError):
        # Обрабатываем ошибку, если в запросе отсутствуют необходимые поля или типы данных не соответствуют ожидаемым
        error_message = {'error': 'Invalid request data'}
        return jsonify(error_message), 400

    except Exception as e:
        # Обрабатываем другие исключения, которые могут возникнуть во время выполнения запроса
        error_message = {'error': str(e)}
        return jsonify(error_message), 500


# Авторизация пользователя
@app.route('/login', methods=['POST'])
def login():
    try:
        # Получаем данные из тела запроса
        data = request.get_json()

        # Проверяем наличие всех необходимых полей в запросе
        if 'email_or_phone' not in data or 'password' not in data:
            raise ValueError('Missing required fields')

        # Ищем пользователя в базе данных по email или phone
        session = Session()

        # Проверяем, является ли значение в поле "email_or_phone" email-адресом
        if '@' in data['email_or_phone']:
            user = session.query(User).filter_by(email=data['email_or_phone']).first()
        else:
            user = session.query(User).filter_by(phone=data['email_or_phone']).first()

        session.close()

        # Проверяем пароль
        if user and user.password == data['password']:

            # Создаем токен
            access_token = generate_access_token(user.id)

            # Возвращаем информацию о пользователе в виде JSON
            result = {'id': user.id, 'full_name': user.full_name, 'email': user.email, 'phone': user.phone, 'created_at': user.created_at, 'access_token': access_token}

            return jsonify(result)
        else:
            # Возвращаем ошибку, если пользователь не найден или пароль неверный
            error_message = {'error': 'Invalid email or password'}
            return jsonify(error_message), 401

    except (ValueError, TypeError):
        # Обрабатываем ошибку, если в запросе отсутствуют необходимые поля или типы данных не соответствуют ожидаемым
        error_message = {'error': 'Invalid request data'}
        return jsonify(error_message), 400

    except Exception as e:
        # Обрабатываем другие исключения, которые могут возникнуть во время выполнения запроса
        error_message = {'error': str(e)}
        return jsonify(error_message), 500


# Маршрут для получения списка товаров
@app.route('/items', methods=['GET'])
def get_items():
    token = request.headers.get('Authorization')

    if token is None:
        return jsonify({'error': 'Unauthorized'}), 401

    user_id = decode_access_token(token)

    if str(user_id).isdigit():
        if user_id is None:
            return jsonify({'error': 'Unauthorized'}), 401

        session = Session()
        user = session.query(User).get(user_id)

        if user is None:
            return jsonify({'error': 'Unauthorized'}), 401

        items = session.query(Product).filter_by(is_active=True).order_by(Product.id).all()
        session.close()

        items_list = []
        for item in items:
            item_data = {
                'id': item.id,
                'name': item.name,
                'price': item.price,
                'created_at': item.created_at,
                'updated_at': item.updated_at
            }
            items_list.append(item_data)

        return jsonify({'items': items_list})
    else:
        return jsonify({'error': 'Unauthorized. '+ user_id}), 401


# Маршрут для получения списка товаров с пагнацией
@app.route('/items_by_page/<int:page>/<int:per_page>', methods=['GET'])
def get_items_by_page(page, per_page):
    token = request.headers.get('Authorization')

    if token is None:
        return jsonify({'error': 'Unauthorized'}), 401

    user_id = decode_access_token(token)

    if str(user_id).isdigit():
        if user_id is None:
            return jsonify({'error': 'Unauthorized'}), 401

        session = Session()
        user = session.query(User).get(user_id)

        if user is None:
            return jsonify({'error': 'Unauthorized'}), 401

        # рассчитываем значения для LIMIT и OFFSET
        offset = (page - 1) * per_page
        limit = per_page

        # выполняем запрос к базе данных с использованием пагинации
        items = session.query(Product).filter(Product.id > offset).order_by(Product.id).limit(limit).all()

        session.close()

        items_list = []
        for item in items:
            item_data = {
                'id': item.id,
                'name': item.name,
                'price': item.price,
                'created_at': item.created_at,
                'updated_at': item.updated_at
            }
            items_list.append(item_data)

        return jsonify({'items': items_list})
    else:
        return jsonify({'error': 'Unauthorized. '+ user_id}), 401


@app.route('/cart')
def get_cart():
    token = request.headers.get('Authorization')

    if token is None:
        return jsonify({'error': 'Unauthorized'}), 401

    user_id = decode_access_token(token)

    if str(user_id).isdigit():
        if user_id is None:
            return jsonify({'error': 'Unauthorized'}), 401

        with Session() as session:
            user = session.query(User).get(user_id)

            if user is None:
                return jsonify({'error': 'Unauthorized'}), 401

            if user.cart is None:
                return jsonify({'error': 'Cart not found'}), 404

            return jsonify({
                'items': [
                    {'product': item.product.name, 'quantity': item.quantity, 'price': item.product.price}
                    for item in user.cart.items
                ],
                'total': user.cart.total()
            })

    else:
        return jsonify({'error': 'Invalid access token'}), 401


# Функция обновления корзины
def update_cart(session, user, data):
    # Получаем данные о товаре из запроса
    product_id = data.get('product_id')
    quantity = data.get('quantity')

    # Получаем товар из базы данных
    product = session.query(Product).filter_by(id=product_id).first()
    if not product:
        raise ValueError('Invalid product ID')

    # Добавляем товар в корзину пользователя
    if not user.cart:
        user.cart = Cart()
        session.add(user.cart)

    # Проверяем, есть ли уже такой продукт в корзине пользователя
    existing_item = session.query(CartItem).filter_by(cart=user.cart, product=product).first()

    if existing_item:
        # Обновляем количество продукта
        existing_item.quantity += quantity
    else:
        # Добавляем новый продукт в корзину
        user.cart.add_item(product, quantity)

    return None


# Маршрут добавления товара или товаров в корзину
@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():

    token = request.headers.get('Authorization')

    if token is None:
        return jsonify({'error': 'Unauthorized'}), 401

    user_id = decode_access_token(token)

    if str(user_id).isdigit():
        if user_id is None:
            return jsonify({'error': 'Unauthorized'}), 401

        with Session() as session:
            user = session.query(User).get(user_id)

            if user is None:
                return jsonify({'error': 'Unauthorized'}), 401

            try:
                data = request.get_json()

                if isinstance(data, dict):

                    update_cart(session, user, data)

                    session.commit()

                    # Возвращаем ответ с обновленной корзиной пользователя
                    result = {'cart': [{'product_id': item.product.id, 'quantity': item.quantity,
                                        'price': item.product.price} for item in user.cart.items]}
                else:
                    for item in data:

                        update_cart(session, user, item)

                    session.commit()

                    # Возвращаем ответ с обновленной корзиной пользователя
                    result = {'cart': [{'product_id': item.product.id, 'quantity': item.quantity,
                                        'price': item.product.price} for item in user.cart.items]}

                return jsonify(result)

            except (ValueError, TypeError) as e:
                session.rollback()
                return jsonify({'error': str(e)}), 400

            finally:
                session.close()

    else:
        return jsonify({'error': 'Invalid access token'}), 401


# Маршрут удаления товара из корзины
@app.route('/remove_from_cart/<int:item_id>/<int:quantity>', methods=['DELETE'])
def remove_from_cart(item_id, quantity):
    token = request.headers.get('Authorization')

    if token is None:
        return jsonify({'error': 'Unauthorized'}), 401

    user_id = decode_access_token(token)

    if str(user_id).isdigit():
        if user_id is None:
            return jsonify({'error': 'Unauthorized'}), 401

        with Session() as session:
            user = session.query(User).get(user_id)

            if user is None:
                return jsonify({'error': 'Unauthorized'}), 401

            try:
                # Получаем товар из базы данных
                product = session.query(Product).filter_by(id=item_id).first()
                if not product:
                    raise ValueError('Invalid product ID')

                # Ищем продукт в корзине пользователя
                existing_item = session.query(CartItem).filter_by(cart=user.cart, product=product).first()
                if existing_item:
                    # Если задано количество больше 0, то уменьшаем его на заданное значение,
                    # иначе удаляем полностью продукт из корзины
                    if quantity > 0:
                        if existing_item.quantity > quantity:
                            existing_item.quantity -= quantity
                        else:
                            session.delete(existing_item)
                    else:
                        session.delete(existing_item)

                    session.commit()

                    # Возвращаем ответ с обновленной корзиной пользователя
                    result = {'cart': [{'product_id': item.product.id, 'quantity': item.quantity,
                                        'price': item.product.price} for item in user.cart.items],
                              'total': user.cart.total()}

                    return jsonify(result)

                else:
                    return jsonify({'error': 'Product not found in cart'}), 404

            except (ValueError, TypeError):
                error_message = {'error': 'Invalid request data'}
                return jsonify(error_message), 400

            except Exception as e:
                error_message = {'error': str(e)}
                return jsonify(error_message), 500

            finally:
                session.close()
    else:
        return jsonify({'error': 'Unauthorized'}), 401


# Маршрут полной очистки корзины
@app.route('/clear_cart', methods=['DELETE'])
def clear_cart():
    token = request.headers.get('Authorization')

    if token is None:
        return jsonify({'error': 'Unauthorized'}), 401

    user_id = decode_access_token(token)

    if str(user_id).isdigit():
        if user_id is None:
            return jsonify({'error': 'Unauthorized'}), 401

        with Session() as session:
            user = session.query(User).get(user_id)

            if user is None:
                return jsonify({'error': 'Unauthorized'}), 401

            try:
                # Удаляем все записи в таблице cart_items, связанные с корзиной пользователя, и саму корзину
                session.query(CartItem).filter(CartItem.cart_id == user.cart.id).delete()
                session.delete(user.cart)
                session.commit()

                # Возвращаем ответ с пустой корзиной пользователя
                result = {'cart': [], 'total_cost': 0}
                return jsonify(result)

            except (ValueError, TypeError):
                error_message = {'error': 'Invalid request data'}
                return jsonify(error_message), 400

            except Exception as e:
                error_message = {'error': str(e)}
                return jsonify(error_message), 500

            finally:
                session.close()
    else:
        return jsonify({'error': 'Unauthorized'}), 401


# Запуск приложения
if __name__ == '__main__':
    app.run(debug=True)