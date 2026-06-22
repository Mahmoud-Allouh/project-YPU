
def get_selection_display_name(key, datas):
    item = list(filter(lambda item: item[0] == key, datas))
    return item[0][1] if item else key
