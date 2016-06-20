# -*- coding: UTF-8 -*-
from budget_app.models import *
from budget_app.loaders import SimpleBudgetLoader
from decimal import *
import csv
import os
import re

class VinarosBudgetLoader(SimpleBudgetLoader):

    # An artifact of the in2csv conversion of the original XLS files is a trailing '.0', which we remove here
    def clean(self, s):
        return s.split('.')[0]

    def parse_item(self, filename, line):
        # Programme codes have changed in 2015, due to new laws. Since the application expects a code-programme
        # mapping to be constant over time, we are forced to amend budget data prior to 2015.
        # See https://github.com/dcabo/presupuestos-aragon/wiki/La-clasificaci%C3%B3n-funcional-en-las-Entidades-Locales
        programme_mapping = {
            # old programme: new programme
            '1320': '1300',
            '1340': '1350',     # Protección Civil
            '1350': '1360',     # Bomberos
            '1550': '1533',     # Brigada
            '1620': '1621',     # Residuos
            '2100': '9200',     # Seguridad Social. TODO: Check. Seems it was not being distributed.
            '2300': '2313',     # Servicios Sociales. TODO: Check
            '2310': '2311',     # Acción Social
            '2320': '2312',     # Promoción Social
            '2340': '2313',     # Mayores
            '3130': '3110',     # Sanidad
            '3210': '3262',     # Servicios complementarios de educación
            '3240': '3262',     # Servicios complementarios de educación
            '3320': '3321',     # Bibliotecas
            '3370': '3380',     # Fiestas populares
            '4310': '4314',     # Comercio
            '4920': '2410',     # Fomento del empleo
            '9250': '3261',     # Juventud
            '9260': '9261',     # Nuevas Tecnologías

        }

        programme_mapping_2015 = {
            # old programme: new programme
            # The 2015 codes don't match the 2016 budget we got in PDF, with programme names
            '1320': '1300', # TODO: Check what's 132
            '1712': '1711', # TODO: Check what's 1712
            '4312': '4314', # TODO: What's 4312

            # And some programmes in 2016 have the same name, for some unknown reason
            '1532': '1533', # Same name for 'Brigada y vías públicas'
            '1600': '1610', # Saneamiento, abastecimiento y distribución de aguas
            '1620': '1621', # Same name for 'Recogida, eliminación y tratamiento residuos'
            '4120': '4100', # Same name for 'Agricultura'
        }

        # Some dirty lines in input data
        if line[0]=='':
            return None

        is_expense = (filename.find('gastos.csv')!=-1)
        is_actual = (filename.find('/ejecucion_')!=-1)
        if is_expense:
            # The input data combines functional and economic codes in a very unusual way
            match = re.search('^(\d+)\. \.(\d+)', line[1])
            # We got 3- or 4- digit functional codes as input, so add a trailing zero
            fc_code = match.group(1).ljust(4, '0')
            ec_code = match.group(2)

            # For years before 2015 we check whether we need to amend the programme code
            year = re.search('municipio/(\d+)/', filename).group(1)
            if int(year) < 2015:
                fc_code = programme_mapping.get(fc_code, fc_code)
            else:
                fc_code = programme_mapping_2015.get(fc_code, fc_code)

            return {
                'is_expense': True,
                'is_actual': is_actual,
                'fc_code': fc_code,
                'ec_code': ec_code[:-2],        # First three digits (everything but last two)
                'ic_code': '000',
                'item_number': ec_code[-2:],    # Last two digits
                'description': line[0],
                'amount': self._parse_amount(line[4 if is_actual else 2])
            }

        else:
            return {
                'is_expense': False,
                'is_actual': is_actual,
                'ec_code': line[1][:3],         # First three digits
                'ic_code': '000',               # All income goes to the root node
                'item_number': line[1][3:5],    # Fourth and fifth digit; careful, there's trailing dirt
                'description': line[0],
                'amount': self._parse_amount(line[4 if is_actual else 2])
            }
