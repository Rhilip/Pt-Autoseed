from http.cookies import SimpleCookie  # Python3 only （Py2: from Cookie import SimpleCookie）


def cookies_raw2jar(raw: str) -> dict:
    """
    Arrange Cookies from raw using SimpleCookies
    """
    cookie = SimpleCookie(raw)
    cookies = {}
    for key, morsel in cookie.items():
        cookies[key] = morsel.value
    return cookies
