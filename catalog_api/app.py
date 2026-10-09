from typing import TypedDict

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class Product(TypedDict):
    id: int
    sku: str
    name: str
    price_cents: int
    available: bool


class CatalogInputError(Exception):
    pass


def create_app() -> FastAPI:
    app = FastAPI(title="Synthetic Catalog QA Demo")
    products: tuple[Product, ...] = (
        {"id": 1, "sku": "DEMO-001", "name": "Inspection kit",
         "price_cents": 2500, "available": True},
        {"id": 2, "sku": "DEMO-002", "name": "Replacement seal",
         "price_cents": 0, "available": False},
        {"id": 3, "sku": "DEMO-003", "name": "Test gauge",
         "price_cents": 1099, "available": True},
    )

    @app.exception_handler(CatalogInputError)
    async def invalid_request(_request: Request, _error: CatalogInputError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={"error": {"code": "INVALID_REQUEST", "message": "Invalid request"}},
        )

    def validate_query(request: Request, allowed: set[str]) -> None:
        keys = list(request.query_params.keys())
        if any(key not in allowed for key in keys):
            raise CatalogInputError()
        if any(len(request.query_params.getlist(key)) != 1 for key in keys):
            raise CatalogInputError()

    @app.get("/health")
    def health(request: Request) -> dict[str, str]:
        validate_query(request, set())
        return {"status": "ok"}

    @app.get("/v1/products")
    def list_products(request: Request) -> list[Product]:
        validate_query(request, {"available"})
        value = request.query_params.get("available")
        if value is not None and value not in ("true", "false"):
            raise CatalogInputError()
        return [
            product.copy() for product in products
            if value is None or product["available"] == (value == "true")
        ]

    @app.get("/v1/products/{product_id}", response_model=None)
    def get_product(product_id: str, request: Request) -> Product | JSONResponse:
        validate_query(request, set())
        # Bound before int conversion, including adversarially long path values.
        if (
            not product_id.isascii() or not product_id.isdecimal()
            or product_id.startswith("0") or len(product_id) > 10
        ):
            raise CatalogInputError()
        identity = int(product_id)
        if identity > 2_147_483_647:
            raise CatalogInputError()
        for product in products:
            if product["id"] == identity:
                return product.copy()
        return JSONResponse(
            status_code=404,
            content={"error": {"code": "PRODUCT_NOT_FOUND", "message": "Product not found"}},
        )

    return app
