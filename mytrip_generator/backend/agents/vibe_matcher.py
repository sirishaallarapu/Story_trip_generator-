def get_trip_vibe(data):
    trip_type = data['trip_type'].lower()
    if trip_type == "adventure":
        return "Thrilling and spontaneous"
    elif trip_type == "romantic":
        return "Charming and intimate"
    elif trip_type == "cultural":
        return "Immersive and educational"
    else:
        return "Relaxed and adventurous"