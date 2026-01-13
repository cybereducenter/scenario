def count_chars(my_str):
    pairs_dict = {}
    for letter in my_str:
        if letter in pairs_dict:
            pairs_dict[letter] += 1
        else:
            pairs_dict[letter] = 1
    return pairs_dict
