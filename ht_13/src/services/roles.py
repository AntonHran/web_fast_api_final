from typing import List

from fastapi import Depends, HTTPException, Request, status

from ht_13.src.database.models_ import User, Role
from ht_13.src.services.auth import auth_user


class RoleAccess:
    def __init__(self, allowed_roles: List[Role]):
        """
        The __init__ function is called when the class is instantiated.
        It sets up the instance of the class, and takes in any arguments that are required to do so.
        In this case, we're taking in a list of allowed roles.

        :param self: Represent the instance of the class
        :param allowed_roles: List[Role]: Specify that the allowed_roles parameter is a list of role objects
        :return: None
        :doc-author: Trelent
        """
        self.allowed_roles = allowed_roles

    async def __call__(self, request: Request, current_user: User = Depends(auth_user.get_current_user)):
        """
        The __call__ function is the function that will be called when a user tries to access this endpoint.
        It takes in two parameters: request and current_user. The request parameter is an object containing
        information about the HTTP Request, such as its method (GET, POST, etc.) and URL. The current_user
        parameter contains information about the currently logged-in user.

        :param self: Access the class attributes
        :param request: Request: Get the request object
        :param current_user: User: Get the current user
        :return: A function that is decorated with the @router
        :doc-author: Trelent
        """
        print(request.method, request.url)
        print(f"User role is {current_user.roles}")
        print(f"Allowed roles: {self.allowed_roles}")
        if current_user.roles not in self.allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operation forbidden")
