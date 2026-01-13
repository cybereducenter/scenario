def count_chars(my_str):
    my_dict = {}
    for char in my_str :
        if char not in my_dict:
            my_dict = {char : my_str.count(char)}
    return my_dict