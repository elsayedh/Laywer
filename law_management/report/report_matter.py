# © 2018 Serpent Consulting Services Pvt. Ltd.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from . import open_png_file
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
import logging
import os
import calendar
from datetime import datetime
from odoo import api, models


_logger = logging.getLogger(__name__)

matplotlib.use('Agg')


class MatterReport(models.AbstractModel):
    _name = 'report.law_management.report_matter'
    _description = 'Matter Report'

    def make_mat_inv_pie_chart(self, matter):
        if matter:
            mat_invoice_ids = self.env['account.move'].search(
                [('matter_id', '=', matter.id)])
            if mat_invoice_ids:
                sizes = list()
                labels = list()
                pay_labels = list()
                for mat_invoice_id in mat_invoice_ids:
                    if mat_invoice_id.invoice_line_ids:
                        total = 0
                        for inv_line_id in mat_invoice_id.invoice_line_ids:
                            total += inv_line_id.quantity
                        lbl_suff = ""
                        pay_lbl = ""
                        if matter.pay_type == 'pay_per_hour':
                            lbl_suff = " " + mat_invoice_id.currency_id.name
                            pay_lbl = "Hrs"
                        lbl = str(mat_invoice_id.amount_total) + lbl_suff
                        labels.append(lbl)
                        sizes.append(mat_invoice_id.amount_total)
                        pay_lbl = str(total) + pay_lbl
                        pay_labels.append(pay_lbl)
                if not sizes or not labels:
                    return False
                patches, texts = plt.pie(sizes, labels=labels, startangle=90)
                plt.legend(patches, pay_labels, loc="best")
                plt.axis('equal')
                plt.tight_layout()
                FN = "/tmp/" + "mat_inv_pie_" + str(matter.id) + ".png"
                plt.savefig(FN, dpi=300, format='png', bbox_inches='tight')
                plt.close()
                # return open(FN, 'rb').read().encode('base64')
                return open_png_file.get_png_file(FN)

    def make_mat_month_bar_chart(self, matter):
        if matter:
            cur_year = datetime.now().year
            objects = list()
            performance = list()
            for month in range(1, 13):
                m_days = calendar.monthrange(cur_year, month)
                m_end_day = m_days[1]
                s_date = "%s-%s-01" % (cur_year, month)
                s_date = datetime.strptime(s_date, "%Y-%m-%d")
                e_date = "%s-%s-%s" % (cur_year, month, m_end_day)
                e_date = datetime.strptime(e_date, "%Y-%m-%d")
                trial_count = self.env['matter.trial'].search_count(
                    [('matter_id', '=', matter.id),
                     ('date', '>=', s_date),
                     ('date', '<=', e_date),
                     ])
                objects.append(datetime.strftime(s_date, "%b"))
                performance.append(int(trial_count))
            if not objects or not performance:
                return False
            objects = tuple(objects)
            y_pos = np.arange(len(objects))
            plt.bar(y_pos, performance, align='center', alpha=0.5)
            plt.xticks(y_pos, objects)
            plt.ylabel('No. of Trials')
            plt.xlabel('Months')
            plt.title('Trials in year' + str(cur_year))
            FN = '/tmp/' + "mat_year_bar" + str(matter.id) + ".png"
            plt.savefig(FN, dpi=300,
                        format='png',
                        bbox_inches='tight')
            plt.close()
            # return open(FN, 'rb').read().encode('base64')
            return open_png_file.get_png_file(FN)

    def make_mat_trails_bar_chart(self, matter):
        if matter:
            objects = list()
            performance = list()
            trail_object = self.env['matter.trial']
            trail_ids = trail_object.search(
                [('matter_id', '=', matter.id)],
                order="date asc")
            for trail_id in trail_ids:
                objects.append(trail_id.name)
                performance.append(trail_id.result)
            if not objects or not performance:
                return False
            objects = tuple(objects)
            y_pos = np.arange(len(objects))
            plt.bar(y_pos, performance, align='center', alpha=0.5)
            plt.xticks(y_pos, objects)
            for i, v in enumerate(performance):
                plt.text(i + .25, v + 3, str(v), color='black',
                         fontweight='normal', ha='center', va='bottom')
            plt.ylabel('Results in percentage')
            plt.xlabel('Trials')
            plt.title('Results')
            FN = '/tmp/' + "mat_trial_bar" + str(matter.id) + ".png"
            plt.savefig(FN, dpi=300,
                        format='png',
                        bbox_inches='tight')
            plt.close()
            # return open(FN, 'rb').read().encode('base64')
            return open_png_file.get_png_file(FN)

    def remove_img(self, matter):
        paths = []
        paths.append("/tmp/" + "mat_inv_pie_" + str(matter.id) + ".png")
        paths.append("/tmp/" + "mat_year_bar" + str(matter.id) + ".png")
        paths.append("/tmp/" + "mat_trial_bar" + str(matter.id) + ".png")
        for path in paths:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except OSError as e:
                    _logger.warning("Error: %s - %s."
                                    % (e.filename, e.strerror))

    @api.model
    def _get_report_values(self, docids, data=None):
        model = self.env.context.get('active_model')
        if data is None:
            data = {}
        if not docids:
            docids = data.get('docids')
        matter = self.env['matter.matter'].browse(docids)
        return {
            'doc_ids': docids,
            'doc_model': model,
            'docs': matter,
            'data': data,
            'make_mat_inv_pie_chart': self.make_mat_inv_pie_chart,
            'make_mat_month_bar_chart': self.make_mat_month_bar_chart,
            'make_mat_trails_bar_chart': self.make_mat_trails_bar_chart,
            'remove_img': self.remove_img,
        }
