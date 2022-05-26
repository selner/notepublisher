def merge(dict_1, dict_2):
    """Merge two dictionaries.

    Values that evaluate to true take priority over falsy values.
    `dict_1` takes priority over `dict_2`.

    """
    return dict((key, dict_1.get(key) or dict_2.get(key))
                for key in set(dict_2) | set(dict_1))

