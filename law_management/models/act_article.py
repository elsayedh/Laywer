# © 2018 Serpent Consulting Services Pvt. Ltd.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import time

from odoo import api, fields, models, _
from odoo.exceptions import UserError

from . import matter


def get_years():
    year_list = []
    last_range = int(time.strftime('%Y')) + 1
    for i in range(1900, last_range):
        year_list.append((str(i), str(i)))
    year_list.sort(reverse=True)
    return year_list


class Act(models.Model):

    _name = 'act.act'
    _description = 'Act'

    _rec_name = 'act_name'

    act_no = fields.Char('Act No')
    act_name = fields.Char('Act Name')
    act_year = fields.Selection(get_years(), 'Year')
    act_desc = fields.Html('Act Description')
    act_type = fields.Selection([('criminal', 'Criminal'), ('civil', 'Civil')],
                                string='Act Type')
    act_category = fields.Selection([('criminal', 'Criminal'),
                                     ('civil', 'Civil')], string='Type')
    act_link = fields.Char('Link')

    def copy(self, default=None):
        """
        This method will restrict duplication access for help desk manager
        ----------------------------------------------------
        @param self : object pointer
        """
        self.ensure_one()
        matter._desk_user(self)
        return super(Act, self).copy(default=default)


class Article(models.Model):

    _name = 'article.article'
    _description = 'Article'
    _rec_name = 'art_name'

    article_no = fields.Char('Article No')
    art_name = fields.Char('Article Name')
    art_link = fields.Char('Link')
    art_notes = fields.Html('Article Description')
    art_category = fields.Selection([('criminal', 'Criminal'),
                                     ('civil', 'Civil')], string='Type')

    def copy(self, default=None):
        """
        This method will restrict duplication access for help desk manager
        ----------------------------------------------------
        @param self : object pointer
        """
        self.ensure_one()
        matter._desk_user(self)
        return super(Article, self).copy(default=default)


class Court(models.Model):
    _name = 'court.court'
    _description = 'Court Details'

    name = fields.Char('Court Name')
    location = fields.Char('Location')

    _sql_constraints = [
        ('name_location', 'unique(name, location)',
         'Court name must be unique per Location!'),
    ]

    def copy(self, default=None):
        """
        This method will restrict duplication access for help desk manager
        ----------------------------------------------------
        @param self : object pointer
        """
        self.ensure_one()
        matter._desk_user(self)
        return super(Court, self).copy(default=default)
