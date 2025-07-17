# Quote calculation logic
def calculate_quote(data: dict):
    total = 0

    if data.get("house_type") == "1-story":
        total += float(data.get("house_sqft", 0)) * 0.25
    elif data.get("house_type") == "2-story":
        total += float(data.get("house_sqft", 0)) * 0.35

    if driveway := data.get("driveway_sqft"):
        sqft = float(driveway)
        if sqft <= 400:
            total += 129
        else:
            total += sqft * 0.35

    if sidewalk := data.get("sidewalk_ft"):
        total += float(sidewalk) * 1.5

    if patio := data.get("patio_sqft"):
        total += float(patio) * 0.40

    if fence := data.get("fence_ft"):
        total += float(fence) * 2.5

    if gutter := data.get("gutter_ft"):
        total += float(gutter) * 2

    if roof := data.get("roof_sqft"):
        total += float(roof) * 0.45

    return round(total, 2)

