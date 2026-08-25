from rest_framework.pagination import PageNumberPagination


class CustomPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"

    def get_paginated_response(self, data):
        return {
            "total": self.page.paginator.count,
            "total_page": self.page.paginator.num_pages,
            "results": data,
            "page": self.page.number,
        }
