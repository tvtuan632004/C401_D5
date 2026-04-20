from .vinfast_cars import VINFAST_CARS


def retrieve(query: str) -> list[str]:
    query = query.lower()
    docs = []

    for car in VINFAST_CARS.values():
        if car["name"].lower().split()[1].lower() in query:
            docs.append(
                f"{car['name']} | Giá: {car['price']} | Tầm hoạt động: {car['range']} | {car['description']}"
            )

    if not docs:
        docs.append(
            "VinFast có các dòng xe điện: VF5, VF6, VF7, VF8, VF9."
        )

    return docs