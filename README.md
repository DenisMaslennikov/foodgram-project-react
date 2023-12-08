# Foodgram

Проект пищевого помощника призван облегчить повседневные хлопоты по 
приготовлению блюд. С помощью продуктового помощника вы сможете делиться 
рецептами, находить новые рецепты составлять списки покупок по выбранным 
рецептам


## Запуск проекта локально
1 Склонируйте репозиторий
```commandline
git clone https://github.com/DenisMaslennikov/foodgram-project-react.git
```
2.1 Для запуска development версии используйте команду
```commandline
docker compose up
```
2.2 Для запуска production версии используйте команду
```commandline
docker compose -f docker-compose.production.yml up
```
## Стек технологий:
Python, Django, Docker, django-filters, sorl-thumbnail

## Примеры запросов к API
1) Регистрация:
```http request
POST /api/users/
{
    "email": email,
    "username": username,
    "first_name": first_name,
    "last_name": last_name,
    "password": password
}
```
2) Авторизация:
```http request
POST /api/auth/token/login/
{
    "email": emal,
    "password": password
}
ответ
{
    "auth_token": token
}
```
3) Создание рецепта:
```http request
POST /api/recipes/
HEADERS {Authorization: you_token}
{
  "ingredients": [
    {
      "id": ingredient_id,
      "amount": int > 1
    }
  ],
  "tags": [
    tag_id,
    tag_id
  ],
  "image": base64_code_image",
  "name": name,
  "text": description,
  "cooking_time": int > 1
}
```
