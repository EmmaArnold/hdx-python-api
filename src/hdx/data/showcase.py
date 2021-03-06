# -*- coding: utf-8 -*-
"""Showcase class containing all logic for creating, checking, and updating showcases."""
import logging
import sys
from os.path import join
from typing import List, Union, Optional, Dict, Any, Tuple

from hdx.utilities import is_valid_uuid
from hdx.utilities.dictandlist import merge_two_dictionaries

import hdx.data.dataset
import hdx.data.hdxobject
import hdx.data.vocabulary
from hdx.hdx_configuration import Configuration

logger = logging.getLogger(__name__)


class Showcase(hdx.data.hdxobject.HDXObject):
    """Showcase class containing all logic for creating, checking, and updating showcases.

    Args:
        initial_data (Optional[Dict]): Initial showcase metadata dictionary. Defaults to None.
        configuration (Optional[Configuration]): HDX configuration. Defaults to global configuration.
    """
    max_int = sys.maxsize
    dataset_ids_field = 'dataset_ids'

    def __init__(self, initial_data=None, configuration=None):
        # type: (Optional[Dict], Optional[Configuration]) -> None
        if not initial_data:
            initial_data = dict()
        super(Showcase, self).__init__(initial_data, configuration=configuration)

    @staticmethod
    def actions():
        # type: () -> Dict[str, str]
        """Dictionary of actions that can be performed on object

        Returns:
            Dict[str, str]: Dictionary of actions that can be performed on object
        """
        return {
            'show': 'ckanext_showcase_show',
            'update': 'ckanext_showcase_update',
            'create': 'ckanext_showcase_create',
            'delete': 'ckanext_showcase_delete',
            'list': 'ckanext_showcase_list',
            'associate': 'ckanext_showcase_package_association_create',
            'disassociate': 'ckanext_showcase_package_association_delete',
            'list_datasets': 'ckanext_showcase_package_list',
            'list_showcases': 'ckanext_package_showcase_list'
        }

    def update_from_yaml(self, path=join('config', 'hdx_showcase_static.yml')):
        # type: (str) -> None
        """Update showcase metadata with static metadata from YAML file

        Args:
            path (Optional[str]): Path to YAML dataset metadata. Defaults to config/hdx_showcase_static.yml.

        Returns:
            None
        """
        super(Showcase, self).update_from_yaml(path)

    def update_from_json(self, path=join('config', 'hdx_showcase_static.json')):
        # type: (str) -> None
        """Update showcase metadata with static metadata from JSON file

        Args:
            path (Optional[str]): Path to JSON dataset metadata. Defaults to config/hdx_showcase_static.json.

        Returns:
            None
        """
        super(Showcase, self).update_from_json(path)

    @staticmethod
    def read_from_hdx(identifier, configuration=None):
        # type: (str, Optional[Configuration]) -> Optional['Showcase']
        """Reads the showcase given by identifier from HDX and returns Showcase object

        Args:
            identifier (str): Identifier of showcase
            configuration (Optional[Configuration]): HDX configuration. Defaults to global configuration.

        Returns:
            Optional[Showcase]: Showcase object if successful read, None if not
        """

        showcase = Showcase(configuration=configuration)
        result = showcase._load_from_hdx('showcase', identifier)
        if result:
            return showcase
        return None

    def check_required_fields(self, ignore_fields=list()):
        # type: (List[str]) -> None
        """Check that metadata for showcase is complete. The parameter ignore_fields should
        be set if required to any fields that should be ignored for the particular operation.

        Args:
            ignore_fields (List[str]): Fields to ignore. Default is [].

        Returns:
            None
        """
        self._check_required_fields('showcase', ignore_fields)

    def update_in_hdx(self, **kwargs):
        # type: (Any) -> None
        """Check if showcase exists in HDX and if so, update it

        Returns:
            None
        """
        self._check_load_existing_object('showcase', 'name')
        # We load an existing object even though it may well have been loaded already
        # to prevent an admittedly unlikely race condition where someone has updated
        # the object in the intervening time
        merge_two_dictionaries(self.data, self.old_data)
        self.clean_tags()
        self._hdx_update('showcase', 'name', force_active=True, **kwargs)
        self._update_in_hdx('showcase', 'name', **kwargs)

    def create_in_hdx(self, **kwargs):
        # type: (Any) -> None
        """Check if showcase exists in HDX and if so, update it, otherwise create it

        Returns:
            None
        """
        if 'ignore_check' not in kwargs:  # allow ignoring of field checks
            self.check_required_fields()
        if 'name' in self.data and self._load_from_hdx('showcase', self.data['name']):
            logger.warning('%s exists. Updating %s' % ('showcase', self.data['name']))
            merge_two_dictionaries(self.data, self.old_data)
            self.clean_tags()
            self._hdx_update('showcase', 'name', force_active=True, **kwargs)
        else:
            self.clean_tags()
            self._save_to_hdx('create', 'title', force_active=True)

        self._create_in_hdx('showcase', 'name', 'title', **kwargs)

    def delete_from_hdx(self):
        # type: () -> None
        """Deletes a showcase from HDX.

        Returns:
            None
        """
        self._delete_from_hdx('showcase', 'id')

    def get_tags(self):
        # type: () -> List[str]
        """Return the dataset's list of tags

        Returns:
            List[str]: List of tags or [] if there are none
        """
        return self._get_tags()

    def add_tag(self, tag, log_deleted=True):
        # type: (str, bool) -> Tuple[List[str], List[str]]
        """Add a tag

        Args:
            tag (str): Tag to add
            log_deleted (bool): Whether to log informational messages about deleted tags. Defaults to True.

        Returns:
            Tuple[List[str], List[str]]: Tuple containing list of added tags and list of deleted tags and tags not added
        """
        return hdx.data.vocabulary.Vocabulary.add_mapped_tag(self, tag, log_deleted=log_deleted)

    def add_tags(self, tags, log_deleted=True):
        # type: (List[str], bool) -> Tuple[List[str], List[str]]
        """Add a list of tags

        Args:
            tags (List[str]): List of tags to add
            log_deleted (bool): Whether to log informational messages about deleted tags. Defaults to True.

        Returns:
            Tuple[List[str], List[str]]: Tuple containing list of added tags and list of deleted tags and tags not added
        """
        return hdx.data.vocabulary.Vocabulary.add_mapped_tags(self, tags, log_deleted=log_deleted)

    def clean_tags(self, log_deleted=True):
        # type: (bool) -> Tuple[List[str], List[str]]
        """Clean tags in an HDX object according to tags cleanup spreadsheet

        Args:
            log_deleted (bool): Whether to log informational messages about deleted tags. Defaults to True.

        Returns:
            Tuple[List[str], List[str]]: Tuple containing list of mapped tags and list of deleted tags and tags not added
        """
        return hdx.data.vocabulary.Vocabulary.clean_tags(self, log_deleted=log_deleted)

    def remove_tag(self, tag):
        # type: (str) -> bool
        """Remove a tag

        Args:
            tag (str): Tag to remove

        Returns:
            bool: True if tag removed or False if not
        """
        return self._remove_hdxobject(self.data.get('tags'), tag.lower(), matchon='name')

    def get_datasets(self):
        # type: () -> List[hdx.data.dataset.Dataset]
        """Get any datasets in the showcase

        Returns:
            List[Dataset]: List of datasets
        """
        assoc_result, datasets_dicts = self._read_from_hdx('showcase', self.data['id'], fieldname='showcase_id',
                                                           action=self.actions()['list_datasets'])
        datasets = list()
        if assoc_result:
            for dataset_dict in datasets_dicts:
                dataset = hdx.data.dataset.Dataset(dataset_dict, configuration=self.configuration)
                datasets.append(dataset)
        return datasets

    def _get_showcase_dataset_dict(self, dataset):
        # type: (Union[hdx.data.dataset.Dataset,Dict,str]) -> Dict
        """Get showcase dataset dict

        Args:
            showcase (Union[Showcase,Dict,str]): Either a showcase id or Showcase metadata from a Showcase object or dictionary

        Returns:
            Dict: showcase dataset dict
        """
        if isinstance(dataset, hdx.data.dataset.Dataset) or isinstance(dataset, dict):
            if 'id' not in dataset:
                dataset = hdx.data.dataset.Dataset.read_from_hdx(dataset['name'])
            dataset = dataset['id']
        elif not isinstance(dataset, str):
            raise hdx.data.hdxobject.HDXError('Type %s cannot be added as a dataset!' % type(dataset).__name__)
        if is_valid_uuid(dataset) is False:
            raise hdx.data.hdxobject.HDXError('%s is not a valid dataset id!' % dataset)
        return {'showcase_id': self.data['id'], 'package_id': dataset}

    def add_dataset(self, dataset, datasets_to_check=None):
        # type: (Union[hdx.data.dataset.Dataset,Dict,str], List[hdx.data.dataset.Dataset]) -> bool
        """Add a dataset

        Args:
            dataset (Union[Dataset,Dict,str]): Either a dataset id or dataset metadata either from a Dataset object or a dictionary
            datasets_to_check (List[Dataset]): List of datasets against which to check existence of dataset. Defaults to datasets in showcase.

        Returns:
            bool: True if the dataset was added, False if already present
        """
        showcase_dataset = self._get_showcase_dataset_dict(dataset)
        if datasets_to_check is None:
            datasets_to_check = self.get_datasets()
        for dataset in datasets_to_check:
            if showcase_dataset['package_id'] == dataset['id']:
                return False
        self._write_to_hdx('associate', showcase_dataset, 'package_id')
        return True

    def add_datasets(self, datasets, datasets_to_check=None):
        # type: (List[Union[hdx.data.dataset.Dataset,Dict,str]], List[hdx.data.dataset.Dataset]) -> bool
        """Add multiple datasets

        Args:
            datasets (List[Union[Dataset,Dict,str]]): A list of either dataset ids or dataset metadata from Dataset objects or dictionaries
            datasets_to_check (List[Dataset]): List of datasets against which to check existence of dataset. Defaults to datasets in showcase.

        Returns:
            bool: True if all datasets added or False if any already present
        """
        if datasets_to_check is None:
            datasets_to_check = self.get_datasets()
        alldatasetsadded = True
        for dataset in datasets:
            if not self.add_dataset(dataset, datasets_to_check=datasets_to_check):
                alldatasetsadded = False
        return alldatasetsadded

    def remove_dataset(self, dataset):
        # type: (Union[hdx.data.dataset.Dataset,Dict,str]) -> None
        """Remove a dataset

        Args:
            dataset (Union[Dataset,Dict,str]): Either a dataset id or dataset metadata either from a Dataset object or a dictionary

        Returns:
            None
        """
        self._write_to_hdx('disassociate', self._get_showcase_dataset_dict(dataset), 'package_id')

    @classmethod
    def search_in_hdx(cls, query='*:*', configuration=None, page_size=1000, **kwargs):
        # type: (Optional[str], Optional[Configuration], int, Any) -> List['Showcase']
        """Searches for datasets in HDX

        Args:
            query (Optional[str]): Query (in Solr format). Defaults to '*:*'.
            configuration (Optional[Configuration]): HDX configuration. Defaults to global configuration.
            page_size (int): Size of page to return. Defaults to 1000.
            **kwargs: See below
            fq (string): Any filter queries to apply
            sort (string): Sorting of the search results. Defaults to 'relevance asc, metadata_modified desc'.
            rows (int): Number of matching rows to return. Defaults to all datasets (sys.maxsize).
            start (int): Offset in the complete result for where the set of returned datasets should begin
            facet (string): Whether to enable faceted results. Default to True.
            facet.mincount (int): Minimum counts for facet fields should be included in the results
            facet.limit (int): Maximum number of values the facet fields return (- = unlimited). Defaults to 50.
            facet.field (List[str]): Fields to facet upon. Default is empty.
            use_default_schema (bool): Use default package schema instead of custom schema. Defaults to False.

        Returns:
            List[Dataset]: list of datasets resulting from query
        """
        curfq = kwargs.get('fq')
        kwargs['fq'] = 'dataset_type:showcase'
        if curfq:
            kwargs['fq'] = '%s AND %s' % (kwargs['fq'], curfq)
        datasets = hdx.data.dataset.Dataset.search_in_hdx(query=query, configuration=configuration,
                                                          page_size=page_size, **kwargs)
        showcases = list()
        for dataset in datasets:
            showcase = Showcase(configuration=configuration)
            showcase.data = dataset.data
            showcase.old_data = dataset.old_data
            showcases.append(showcase)
        return showcases

    @classmethod
    def get_all_showcases(cls, configuration=None, page_size=1000, **kwargs):
        # type: (Optional[Configuration], int, Any) -> List['Showcase']
        """Get all showcases in HDX

        Args:
            configuration (Optional[Configuration]): HDX configuration. Defaults to global configuration.
            page_size (int): Size of page to return. Defaults to 1000.
            **kwargs: See below
            rows (int): Number of rows to return. Defaults to all showcases (sys.maxsize)
            start (int): Offset in the complete result for where the set of returned showcases should begin

        Returns:
            List[Showcase]: list of all showcases in HDX
        """
        return cls.search_in_hdx(configuration=configuration, page_size=page_size, **kwargs)
