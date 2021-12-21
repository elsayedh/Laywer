# © 2018 Serpent Consulting Services Pvt. Ltd.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from . import open_png_file
from odoo import api, models
import numpy as np
import matplotlib.pyplot as plt
import logging
import os
from datetime import datetime

import matplotlib
matplotlib.use('Agg')


_logger = logging.getLogger(__name__)


class LawyerReport(models.AbstractModel):
    _name = 'report.law_management.report_lawyer'
    _description = 'Lawyer Report'

    def make_bar_chart(self, lawyer):
        if lawyer:
            objects = ('Assigned', 'Won', 'Lost', 'Settled', 'Total',)
            y_pos = np.arange(len(objects))
            performance = [lawyer.case_assign,
                           lawyer.case_won,
                           lawyer.case_lost,
                           lawyer.case_settle,
                           lawyer.tot_cases, ]
            if not objects or not performance:
                return False
            plt.bar(y_pos, performance, align='center', alpha=0.5)
            plt.xticks(y_pos, objects)
            plt.ylabel('No of Cases')
            plt.xlabel('Category')
            plt.title('Matter Details')
            FN = '/tmp/' + str(lawyer.id) + ".png"
            plt.savefig(FN, dpi=300, format='png', bbox_inches='tight')
            # use format='svg' or 'pdf' for vectorial picturesN
            plt.close()
            # return open(FN, 'rb').read().encode('base64')
            return open_png_file.get_png_file(FN)

    def make_matter_year_bar_chart(self, lawyer):
        if lawyer:
            # Code is to print all matters of lawyer
            # start_date = self.env['matter.matter'].search([('assign_id', '='\
            # , lawyer.id)], order="date_open asc",\
            #                              limit=1).date_open
            # end_date = self.env['matter.matter'].search([('assign_id', '=',\
            #                 lawyer.id)], order="date_open desc",\
            #                              limit=1).date_open
            # if start_date and end_date:
            #    start_year = datetime.strptime(start_date, "%Y-%m-%d").year
            #    end_year = datetime.strptime(end_date, "%Y-%m-%d").year
            #    years = list()
            #    for year in range(start_year, end_year + 1):
            #        years.append(year)

            # Code to print current year's metter of lawyer
            cur_year = datetime.now().year
            years = list()
            for year in range((cur_year - 10), (cur_year + 1)):
                years.append(year)
            if years:
                objects = list()
                performance = list()
                for year in years:
                    s_date = "%s-01-01" % year
                    s_date = datetime.strptime(s_date, "%Y-%m-%d")
                    e_date = "%s-12-31" % year
                    e_date = datetime.strptime(e_date, "%Y-%m-%d")
                    case_count = self.env['matter.matter'].search_count(
                        [('assign_id', '=', lawyer.id),
                         ('date_open', '>=', s_date),
                         ('date_open', '<=', e_date),
                         ])
                    objects.append(year)
                    performance.append(int(case_count))
                if not objects or not performance:
                    return False
                objects = tuple(objects)
                y_pos = np.arange(len(objects))
                plt.bar(y_pos, performance, align='center', alpha=0.5)
                plt.xticks(y_pos, objects)
                plt.ylabel('No of Cases')
                plt.xlabel('Year')
                plt.title('Matters for Last 10 Years')
                FN = '/tmp/' + "mat_year_bar" + str(lawyer.id) + ".png"
                plt.savefig(FN, dpi=300, format='png', bbox_inches='tight')
                plt.close()
                # return open(FN, 'rb').read().encode('base64')
                return open_png_file.get_png_file(FN)

    def make_pie_chart(self, lawyer):
        if lawyer:
            if not lawyer.spec_ids:
                return False
            if lawyer.spec_ids:
                labels = list()
                for spec_id in lawyer.spec_ids:
                    labels.append(spec_id.name)
                sizes = [1]
                len_labels = len(labels)
                sizes = sizes * len_labels
                patches, texts = plt.pie(sizes, startangle=90)
                plt.legend(patches, labels, loc="best")
                plt.axis('equal')
                plt.tight_layout()
                plt.title('Practice Areas')
                FN = '/tmp/' + "pie_" + str(lawyer.id) + ".png"
                plt.savefig(FN, dpi=300, format='png', bbox_inches='tight')
                # use format='svg' or 'pdf' for vectorial picturesN
                plt.close()
                # return open(FN, 'rb').read().encode('base64')
                return open_png_file.get_png_file(FN)

    def make_matter_pie_chart(self, lawyer):
        matter_obj = self.env['matter.matter']
        if lawyer:
            sizes = list()
            labels = list()
            states = ['settlement', 'progress', 'win', 'lost', ]
            for state in states:
                matter_count = matter_obj.search_count(
                    [('assign_id', '=', lawyer.id),
                     ('state', '=', state)])
                if matter_count > 0:
                    sizes.append(int(matter_count))
                    labels.append(state.title())
            if 'Win' in labels:
                index = labels.index('Win')
                labels[index] = 'Won'
            if not sizes:
                return False
            plt.pie(sizes, labels=labels,
                    autopct='%1.1f%%', startangle=140)

            plt.axis('equal')
            FN = '/tmp/' + "mat_pie_" + str(lawyer.id) + ".png"
            plt.savefig(FN, dpi=300, format='png', bbox_inches='tight')
            # use format='svg' or 'pdf' for vectorial picturesN
            plt.close()
            # return open(FN, 'rb').read().encode('base64')
            return open_png_file.get_png_file(FN)

    def remove_img(self, lawyer_id):
        paths = []
        paths.append('/tmp/' + str(lawyer_id) + ".png")
        paths.append('/tmp/' + "pie_" + str(lawyer_id) + ".png")
        paths.append('/tmp/' + "mat_pie_" + str(lawyer_id) + ".png")
        paths.append('/tmp/' + "mat_year_bar" + str(lawyer_id) + ".png")
        for path in paths:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except OSError as e:
                    _logger.warning("Error: %s - %s."
                                    % (e.filename, e.strerror))

    def maximum_trails_one_matter(self, lawyer_id):
        if lawyer_id:
            matter_obj = self.env['matter.matter']
            trial_obj = self.env['matter.trial']
            matter_ids = matter_obj.search([('assign_id', '=', lawyer_id.id)])
            max_trail_count = 0
            for matter_id in matter_ids:
                trail_count = trial_obj.search_count(
                    [('matter_id', '=', matter_id.id)])
                if trail_count > max_trail_count:
                    max_trail_count = trail_count
            return max_trail_count

    @api.model
    def _get_report_values(self, docids, data=None):
        model = self.env.context.get('active_model')
        if data is None:
            data = {}
        if not docids:
            docids = data.get('docids')
        employee = self.env['hr.employee'].browse(docids)
        return {
            'doc_ids': docids,
            'doc_model': model,
            'docs': employee,
            'data': data,
            'make_bar_chart': self.make_bar_chart,
            'remove_img': self.remove_img,
            'make_pie_chart': self.make_pie_chart,
            'make_matter_pie_chart': self.make_matter_pie_chart,
            'make_matter_year_bar_chart': self.make_matter_year_bar_chart,
            'maximum_trails_one_matter': self.maximum_trails_one_matter,
        }
