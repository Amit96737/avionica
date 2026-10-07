from fastapi import Query, HTTPException
from typing import Optional
from sqlalchemy.orm import Query as SAQuery
from fastapi import Request


class PageNumberPagination:
    def __init__(
            self,
            page: int = Query(1, ge=1, description="Page number"),
            # page_size: int = Query(20, ge=1, le=100, description="Items per page"),
            page_size: int = 20,
            max_page_size: int = 20,
    ):
        self.page = page
        # self.page_size = min(page_size, max_page_size)
        self.page_size = 20
        self.max_page_size = max_page_size

    def paginate_query(self, query: SAQuery) -> SAQuery:
        offset = (self.page - 1) * self.page_size
        return query.offset(offset).limit(self.page_size)

    def get_paginated_response(
            self,
            data,
            total_count: int,
            request: Optional[Request] = None,
            detail: str = "action completed successfully"

    ):
        # base_url = str(request.url).split("?")[0] if request else ""
        # query_params = dict(request.query_params) if request else {}

        # def build_url(page_num):
        #     if page_num < 1 or (total_count and (page_num - 1) * self.page_size >= total_count):
        #         return None
        #     query_params['page'] = str(page_num)
        #     return base_url + "?" + "&".join(f"{k}={v}" for k, v in query_params.items())

        total_pages = int(total_count / self.max_page_size)
        if total_count > (total_pages * self.max_page_size):
            total_pages += 1

        # if self.page > total_pages:
        #     raise HTTPException(status_code=400, detail="Page not found. You have exceeded the maximum number of pages.")

        response = {'detail': detail, "count": total_count, 'total_pages': total_pages, "next": self.page + 1, "previous": self.page - 1,
                    "results": data}
        return response
