# -*- coding: utf-8 -*-
"""Helper to the Dataset class for handling processing dataset titles.
"""
import logging
import re
from datetime import datetime, timedelta
from parser import ParserError
from string import punctuation, whitespace

import six
from typing import List, Tuple, Optional, Match

if six.PY2:
    from quantulum import parser
else:
    from quantulum3 import parser

from hdx.utilities.dateparse import parse_date_range, parse_date
from hdx.utilities.text import remove_end_characters, remove_from_end, PUNCTUATION_MINUS_BRACKETS, remove_string

logger = logging.getLogger(__name__)


class DatasetTitleHelper(object):
    YEAR_RANGE_PATTERN = re.compile(r'([12]\d\d\d)(/(\d{1,2}))?(-| & | and )([12]\d\d\d)')
    YEAR_RANGE_PATTERN2 = re.compile(r'([12]\d\d\d)([/-])(\d{1,2})')
    YEAR_PATTERN = re.compile(r'([12]\d\d\d)')
    PUNCTUATION_PATTERN = re.compile(r'[%s]' % punctuation)
    EMPTY_BRACKET_PATTERN = re.compile(r'(\s?\(\s*\)\s?)')
    WORD_RIGHT_BRACKET_PATTERN = re.compile(r'\b(\s*)(\w{2,})\b\)')
    DATE_INTRO_WORDS = ['on', 'at', 'for', 'of', 'in']

    @classmethod
    def fuzzy_match_dates_in_title(cls, title, ranges, ignore_wrong_years):
        # type: (str, List[Tuple[datetime,datetime]], List[int]) -> str
        """
        Fuzzy match dates in title appending to ranges

        Args:
            title (str): Title to parse
            ranges (List[Tuple[datetime,datetime]]): List of date ranges found so far
            ignore_wrong_years (List[int]): Numbers identified as years that probably are not years

        Returns:
            str: Title with dates removed

        """
        try:
            for quant in parser.parse(title):
                if quant.unit.name == 'dimensionless':
                    continue
                ignore_wrong_years.append(int(quant.value))
        except UnboundLocalError:  # quantulum on Py2 has a bug
            pass
        for match in cls.YEAR_PATTERN.finditer(title):
            year = match.group(0)
            if int(year) in ignore_wrong_years:
                continue
            start = match.start()
            end = match.end()
            stringlr = title[max(start - 13, 0):end]
            fuzzylr = dict()
            startdatelr = None
            enddatelr = None
            deltalr = timedelta(days=1000)
            try:
                startdatelr, enddatelr = parse_date_range(stringlr, fuzzy=fuzzylr, zero_time=True)
                if startdatelr and enddatelr:
                    deltalr = enddatelr - startdatelr
            except ParserError:
                pass
            fuzzyrl = dict()
            stringrl = title[start:min(end + 13, len(title))]
            startdaterl = None
            enddaterl = None
            deltarl = timedelta(days=1000)
            try:
                startdaterl, enddaterl = parse_date_range(stringrl, fuzzy=fuzzyrl, zero_time=True)
                if startdaterl and enddaterl:
                    deltarl = enddaterl - startdaterl
            except ParserError:
                pass
            if startdatelr and deltalr <= deltarl:
                date_components = fuzzylr['date']
                ranges.append((startdatelr, enddatelr))
            elif startdaterl:
                date_components = fuzzyrl['date']
                ranges.append((startdaterl, enddaterl))
            else:
                date_components = (year)
                ranges.append(parse_date_range(year, zero_time=True))
            newtitle = title
            for date_component in date_components:
                newtitle = remove_string(newtitle, date_component, PUNCTUATION_MINUS_BRACKETS)
            logger.info('Removing date from title: %s -> %s' % (title, newtitle))
            title = newtitle
        try:
            fuzzy = dict()
            startdate, enddate = parse_date_range(title, fuzzy=fuzzy, zero_time=True)
            if startdate == enddate and len(fuzzy['date']) == 1:  # only accept dates where day, month and year are
                # all together not split throughout the string and where the date is a precise day not a range
                ranges.append((startdate, enddate))
                date_component = fuzzy['date'][0]
                newtitle = remove_string(title, date_component, PUNCTUATION_MINUS_BRACKETS)
                logger.info('Removing date from title: %s -> %s' % (title, newtitle))
                title = newtitle
        except (ParserError, OverflowError):
            pass

        return title

    @classmethod
    def get_month_year_in_slash_range(cls, match, ignore_wrong_years):
        # type: (Match, List[int]) -> Tuple[Optional[int], Optional[int], Optional[int]]
        """
        Get year(s) and month from slash range eg. 2007/08. If second value is between 1 and 12, take it as a month.

        Args:
            match (Match): Match object
            ignore_wrong_years (List[int]): Numbers identified as years that probably are not years

        Returns:
            Tuple[Optional[int], Optional[int], Optional[int]]: First year, first month, second year

        """
        first_year_str = match.group(1)
        first_year = int(first_year_str)
        if first_year in ignore_wrong_years:
            return None, None, None
        two_digits_str = match.group(3)
        if two_digits_str:
            two_digits = int(two_digits_str)
            if 1 <= two_digits <= 12:
                return first_year, two_digits, None
            else:
                second_year = int('%s%s' % (first_year_str[:2], two_digits_str))
                if second_year > first_year:
                    return first_year, None, second_year
                else:
                    ignore_wrong_years.append(first_year)
                    return None, None, None
        else:
            return first_year, None, None

    @classmethod
    def get_dates_from_title(cls, title):
        # type: (str) -> Tuple[str,List[Tuple[datetime,datetime]]]
        """
        Get dataset dates (start and end dates in a list) from title and clean title of dates

        Args:
            title (str): Title to get date from and clean

        Returns:
            Tuple[str,List[Tuple[datetime,datetime]]]: Cleaned title, list of start and end dates

        """
        ranges = list()
        ignore_wrong_years = list()
        for match in cls.YEAR_RANGE_PATTERN.finditer(title):
            first_year, first_month, second_year = cls.get_month_year_in_slash_range(match, ignore_wrong_years)
            if first_year is None:
                continue
            if first_month is None:
                first_month = 1
            startdate = parse_date('%d-%d-01' % (first_year, first_month), '%Y-%m-%d', zero_time=True)
            enddate = parse_date('%s-12-31' % match.group(5), '%Y-%m-%d', zero_time=True)
            ranges.append((startdate, enddate))
            newtitle = remove_string(title, match.group(0))
            logger.info('Removing date range from title: %s -> %s' % (title, newtitle))
            title = newtitle

        for match in cls.YEAR_RANGE_PATTERN2.finditer(title):
            first_year, first_month, second_year = cls.get_month_year_in_slash_range(match, ignore_wrong_years)
            if first_year is None or second_year is None:
                continue
            startdate = parse_date('%d-01-01' % first_year, '%Y-%m-%d', zero_time=True)
            enddate = parse_date('%d-12-31' % second_year, '%Y-%m-%d', zero_time=True)
            ranges.append((startdate, enddate))
            newtitle = remove_string(title, match.group(0))
            logger.info('Removing date range from title: %s -> %s' % (title, newtitle))
            title = newtitle

        title = cls.fuzzy_match_dates_in_title(title, ranges, ignore_wrong_years)

        for match in cls.WORD_RIGHT_BRACKET_PATTERN.finditer(title):
            word = match.group(2)
            if word in cls.DATE_INTRO_WORDS:
                title = title.replace(match.group(0), ')')

        for match in cls.EMPTY_BRACKET_PATTERN.finditer(title):
            title = title.replace(match.group(0), ' ')
        title = remove_end_characters(title, '%s%s' % (PUNCTUATION_MINUS_BRACKETS, whitespace))
        title = remove_from_end(title, ['as of'] + cls.DATE_INTRO_WORDS, 'Removing - from title: %s -> %s')
        return title, sorted(ranges)
