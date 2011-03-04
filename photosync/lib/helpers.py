"""Helper functions

Consists of functions to typically be used within templates, but also
available to Controllers. This module is available to templates as 'h'.
"""
# Import helpers as desired, or define your own, ie:
#from webhelpers.html.tags import checkbox, password

from webhelpers.html.tags import form, submit, end_form, select, text, checkbox

from webhelpers.date import distance_of_time_in_words, time_ago_in_words
