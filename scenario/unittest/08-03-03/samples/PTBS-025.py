def count_chars(my_str):
    """
    function gets a string and returns a dictonary, every pair in the dictonary includes the letter and how many times it appeard on the string
    :param: my_str
    :type: the string
    :return: chars_dict - the dictonary of letters and how many times the appeard
    :rtype: dictonaty
    """
    chars_dict = {}
    for char in my_str:
        char = char.lower()
        if char.isalpha():
            if char in chars_dict:
                chars_dict[char] += 1
            else:
                chars_dict[char] = 1
    return chars_dict