from .vinfast_cars import VINFAST_CARS


def retrieve(query: str) -> list[str]:
    query = query.lower()
    docs = []

    for car in VINFAST_CARS.values():
        model_name = car["name"].lower().split()[1].lower()  # vf5, vf6...
        if model_name in query:
            docs.append(
                f"{car['name']} | Giá: {car['price']} | Tầm hoạt động: {car['range']} | {car['description']}"
            )

    return docs