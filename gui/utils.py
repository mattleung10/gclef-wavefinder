# UI utility functions

def valid_int(i_str : str):
    """Check if a int value is valid"""
    try:
        float(i_str)
    except:
        return False
    else:
        return True

def valid_float(f_str : str):
    """Check if a float value is valid"""
    try:
        float(f_str)
    except:
        return False
    else:
        return True