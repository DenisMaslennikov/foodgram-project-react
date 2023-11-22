from pathlib import Path

# Настройка параметров модели пользователя.
EMAIL_MAX_LEN = 254
USERNAME_MAX_LEM = 150
FIRST_NAME_MAX_LEN = 150
LAST_NAME_MAX_LEN = 150

# Настройки генерации PDF документа для корзины покупок.

BASE_DIR = Path(__file__).resolve().parent.parent
PDF_FONT_DIR = BASE_DIR / 'fonts'
PDF_FONT_FILE = 'arial.ttf'
PDF_FONT_NAME = 'Arial'

PDF_INDENT = 72
PDF_TITLE_FONT_SIZE = 15
PDF_TEXT_FONT_SIZE = 12
PDF_GAP = 3

# Настройка пагинации по умолчанию.

DEFAULT_PAGINATION_PAGE_SIZE = 20

# Настройка валидации сериализатора рецептов.
MIN_INGREDIENT_AMOUNT = 1
MIN_COOKING_TIME = 1
