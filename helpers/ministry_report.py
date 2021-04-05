from datetime import datetime
from tempfile import NamedTemporaryFile
from constants import DAYS_WITHOUT_REPORT
import math
import re
import tabula
from pandas_ods_reader import read_ods
from abc import ABC, abstractmethod
import requests


class GenericMinistryReport(ABC):

    def __init__(self, date, page, area=None):
        self._date = date
        self._page = page
        self._area = area
        self._data_frame = None

    @property
    def data_frame(self):
        if self._data_frame is None:
            col2str = {'dtype': str}
            data_frames = tabula.read_pdf(self._get_url(), pages=str(self._page), area=self._area,
                                          pandas_options=col2str)
            self._data_frame = list(filter(lambda x: len(x) >= 19, data_frames))[0]

            for column in self._data_frame:
                self._data_frame[column.replace('*', '').strip()] = self._data_frame.pop(column)

        return self._data_frame

    @abstractmethod
    def _get_url(self):
        pass

    def get_column_data(self, column, part=0, cast=int, num_rows=19):
        first_column = self.data_frame.columns[0]
        ccaas_column = self.data_frame[first_column].astype(str)
        first_ccaa_position = ccaas_column.loc[ccaas_column.str.startswith('Andalucía', na=False)].index[0]

        cases = {}
        for i in range(first_ccaa_position, first_ccaa_position + num_rows):
            ccaa = self.data_frame[first_column][i].replace('*', '').replace('(', '').replace(')', '').replace('Leon', 'León').strip().replace('\r', ' ').replace('-', '').replace(' arra', 'arra')
            ccaa = ' '.join(ccaa.split())
            value_str = str(self.data_frame[self.data_frame.columns[column]][i]).split(' ')[part]
            value_str = re.sub("\\.0$", "", value_str)
            value = value_str.replace('.', '').replace('-', '0').replace(',', '.').replace('%', '')
            cases[ccaa] = cast(value)

        return cases


class SpainCovid19MinistryReport(GenericMinistryReport):

    PDF_URL_FORMAT = "https://www.mscbs.gob.es/en/profesionales/saludPublica/ccayes/alertasActual/nCov-China/" \
                     "documentos/Actualizacion_{0}_COVID-19.pdf"

    def _get_url(self):
        return self.PDF_URL_FORMAT.format(self.get_cases_pdf_id_for_date(self._date))

    @staticmethod
    def get_cases_pdf_id_for_date(date):
        # 14/5/2020 -> id: 105
        # Starting on 4/7/2020, Spanish Public Health Ministry does not publish reports at weekends.
        reference_date = datetime(2020, 5, 14)
        initial_weekend_without_report = datetime(2020, 7, 4)
        weekends = math.ceil((date - initial_weekend_without_report).days / 7) \
            if date > initial_weekend_without_report else 0
        pdf_id = 105 + (date - reference_date).days - weekends * 2

        for day_without_report in DAYS_WITHOUT_REPORT:
            if date.date() > day_without_report:
                pdf_id -= 1

        return pdf_id


class VaccinesMinistryReport(GenericMinistryReport):

    VACCINES_URL_FORMAT = "https://www.mscbs.gob.es/profesionales/saludPublica/ccayes/alertasActual/nCov/documentos/" \
                          "Informe_Comunicacion_{0}.ods"

    def _get_url(self):
        date_str = self._date.strftime("%Y%m%d")
        return self.VACCINES_URL_FORMAT.format(date_str)

    @property
    def data_frame(self):
        if self._data_frame is None:
            with NamedTemporaryFile(mode='wb', suffix=".ods") as f:
                req = requests.get(self._get_url())
                req.raise_for_status()
                f.write(req.content)
                f.flush()

                self._data_frame = read_ods(f.name, self._page)

        return self._data_frame
