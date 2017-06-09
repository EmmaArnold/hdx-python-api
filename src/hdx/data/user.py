# -*- coding: utf-8 -*-
"""User class containing all logic for creating, checking, and updating users."""
import logging
from os.path import join
from typing import Optional

from hdx.data.hdxobject import HDXObject

logger = logging.getLogger(__name__)


class User(HDXObject):
    """User class containing all logic for creating, checking, and updating users.

    Args:
        initial_data (Optional[dict]): Initial user metadata dictionary. Defaults to None.
        configuration (Optional[Configuration]): HDX configuration. Defaults to global configuration.
    """

    def __init__(self, initial_data=None, configuration=None):
        # type: (Optional[dict], Optional[Configuration]) -> None
        if not initial_data:
            initial_data = dict()
        super(User, self).__init__(initial_data, configuration=configuration)

    @staticmethod
    def actions():
        # type: () -> dict
        """Dictionary of actions that can be performed on object

        Returns:
            dict: Dictionary of actions that can be performed on object
        """
        return {
            'show': 'user_show',
            'update': 'user_update',
            'create': 'user_create',
            'delete': 'user_delete',
            'list': 'user_list'
        }

    def update_from_yaml(self, path=join('config', 'hdx_user_static.yml')):
        # type: (str) -> None
        """Update user metadata with static metadata from YAML file

        Args:
            path (Optional[str]): Path to YAML dataset metadata. Defaults to config/hdx_user_static.yml.

        Returns:
            None
        """
        super(User, self).update_from_yaml(path)

    def update_from_json(self, path=join('config', 'hdx_user_static.json')):
        # type: (str) -> None
        """Update user metadata with static metadata from JSON file

        Args:
            path (Optional[str]): Path to JSON dataset metadata. Defaults to config/hdx_user_static.json.

        Returns:
            None
        """
        super(User, self).update_from_json(path)

    @staticmethod
    def read_from_hdx(identifier, configuration=None):
        # type: (str, Optional[Configuration]) -> Optional['User']
        """Reads the user given by identifier from HDX and returns User object

        Args:
            identifier (str): Identifier of user
            configuration (Optional[Configuration]): HDX configuration. Defaults to global configuration.

        Returns:
            Optional[User]: User object if successful read, None if not
        """

        user = User(configuration=configuration)
        result = user._load_from_hdx('user', identifier)
        if result:
            return user
        return None

    def check_required_fields(self, ignore_fields=list()):
        # type: (List[str]) -> None
        """Check that metadata for user is complete. The parameter ignore_fields should
        be set if required to any fields that should be ignored for the particular operation.

        Args:
            ignore_fields (List[str]): Fields to ignore. Default is [].

        Returns:
            None
        """
        self._check_required_fields('user', ignore_fields)

    def update_in_hdx(self):
        # type: () -> None
        """Check if user exists in HDX and if so, update user

        Returns:
            None
        """
        self._update_in_hdx('user', 'id')

    def create_in_hdx(self):
        # type: () -> None
        """Check if user exists in HDX and if so, update it, otherwise create user

        Returns:
            None
        """
        self._create_in_hdx('user', 'id', 'name')

    def delete_from_hdx(self):
        # type: () -> None
        """Deletes a user from HDX.

        Returns:
            None
        """
        self._delete_from_hdx('user', 'id')

    @staticmethod
    def get_all_users(configuration=None, **kwargs):
        # type: (Optional[Configuration], ...) -> List['User']
        """Get all users in HDX

        Args:
            configuration (Optional[Configuration]): HDX configuration. Defaults to global configuration.
            **kwargs: See below
            q (str): Restrict to names containing a string. Defaults to all users.
            order_by (str): Field by which to sort - any user field or edits (number_of_edits). Defaults to 'name'.

        Returns:
            List[User]: List of all users in HDX
        """
        user = User(configuration=configuration)
        user['id'] = 'all users'  # only for error message if produced
        result = user._write_to_hdx('list', kwargs, 'id')
        users = list()
        if result:
            for userdict in result:
                user = User(userdict, configuration=configuration)
                users.append(user)
        else:
            logger.debug(result)
        return users
