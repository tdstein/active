import re


def interpolate(template: str, **kwargs) -> str:
    """
    Interpolate a template string with values provided as keyword arguments.

    Takes a template string containing placeholders in the format `:variable_name` and replaces them with the values provided as keyword arguments. Placeholders are identified by a leading colon `:` followed by a variable name. The placeholder is substitued for the corresponding value in the keyword arguments.

    Arguments:
        template (str): The template string containing placeholders in the format `:variable_name`.
        **kwargs: Key-value pairs where the key corresponds to the placeholder name (without the colon) and the value is value to substitute with.

    Returns:
        str

    Raises:
        KeyError: If the template contains a placeholder without a corresponding key in the provided kwargs.

    Example:
        >>> interpolate("/posts/:id/comments/:comment_id", id=1, comment_id=1)
        '/posts/1/comments/1'
    """

    def replace(match):
        key = match.group(1)
        if key in kwargs:
            return str(kwargs[key])
        else:
            raise KeyError(f"Key '{key}' not found in values.")

    return re.sub(r":(\w+)", replace, template)
