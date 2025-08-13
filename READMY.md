# Документация по API эндпоинтам

## Базовый URL
`http://yourdomain.com/api/v1`

## Аутентификация

### 1. Логин (получение токена)
**Эндпоинт**: `POST /auth/login`  
**Теги**: auth  
**Описание**: Получение JWT токена для аутентификации  
**Требует аутентификации**: Нет  

**Параметры запроса (form-data)**:
- `username` (string, required) - Email пользователя
- `password` (string, required) - Пароль пользователя

**Пример ответа (200 OK)**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Ошибки**:
- 401 Unauthorized - Неверные учетные данные

---

### 2. Регистрация пользователя
**Эндпоинт**: `POST /register`  
**Теги**: auth  
**Описание**: Создание нового пользователя  
**Требует аутентификации**: Нет  

**Тело запроса (JSON)**:
```json
{
  "email": "user@example.com",
  "password": "string",
  "confirm_password": "string"
}
```

**Пример ответа (200 OK)**:
```json
{
  "email": "user@example.com",
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "hashed_password": "$2b$12$...",
  "is_active": true,
  "created_at": "2023-01-01T00:00:00",
  "avatar": null,
  "vk_id": null,
  "google_id": null
}
```

**Ошибки**:
- 400 Bad Request - Email уже зарегистрирован
- 422 Unprocessable Entity - Невалидные данные

---

### 3. Получение информации о текущем пользователе
**Эндпоинт**: `GET /me`  
**Теги**: auth  
**Описание**: Получение информации о текущем аутентифицированном пользователе  
**Требует аутентификации**: Да (JWT токен)  

**Заголовки**:
- `Authorization: Bearer <token>`

**Пример ответа (200 OK)**:
```json
{
  "email": "user@example.com",
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "hashed_password": "$2b$12$...",
  "is_active": true,
  "created_at": "2023-01-01T00:00:00",
  "avatar": null,
  "vk_id": null,
  "google_id": null
}
```

**Ошибки**:
- 401 Unauthorized - Невалидный токен
- 403 Forbidden - Пользователь неактивен

---

## Пользователи

### 1. Получение информации о пользователе
**Эндпоинт**: `GET /users/{user_id}`  
**Теги**: users  
**Описание**: Получение информации о конкретном пользователе  
**Требует аутентификации**: Да (JWT токен)  

**Параметры пути**:
- `user_id` (UUID, required) - ID пользователя

**Заголовки**:
- `Authorization: Bearer <token>`

**Пример ответа (200 OK)**:
```json
{
  "email": "user@example.com",
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "hashed_password": "$2b$12$...",
  "is_active": true,
  "created_at": "2023-01-01T00:00:00",
  "avatar": null,
  "vk_id": null,
  "google_id": null
}
```

**Ошибки**:
- 401 Unauthorized - Невалидный токен
- 403 Forbidden - Нет прав доступа к этому пользователю
- 404 Not Found - Пользователь не найден

---

## Health Check

### 1. Проверка работоспособности сервиса
**Эндпоинт**: `GET /health`  
**Описание**: Проверка доступности сервиса  
**Требует аутентификации**: Нет  

**Пример ответа (200 OK)**:
```json
{
  "status": "healthy"
}
```

---

## Примечания
1. Все запросы, требующие аутентификации, должны включать JWT токен в заголовке `Authorization: Bearer <token>`
2. Для регистрации пароль и подтверждение пароля должны совпадать
3. Время жизни access токена - 30 минут (настраивается в конфигурации)
4. Все даты возвращаются в формате ISO 8601 (UTC)