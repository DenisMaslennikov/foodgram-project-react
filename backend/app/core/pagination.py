from rest_framework.pagination import PageNumberPagination

from foodgram_backend import constants


class FoodgramPaginator(PageNumberPagination):
    page_size_query_param = 'limit'
    page_size = constants.DEFAULT_PAGINATION_PAGE_SIZE
