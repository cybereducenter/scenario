def count_chars(my_str):
    my_dict = {}
    for c in my_str:
        if c != ' ':
            if c in my_dict:
                my_dict[c] = my_dict[c] + 1
            else:
                my_dict[c] = 1
    return my_dict
