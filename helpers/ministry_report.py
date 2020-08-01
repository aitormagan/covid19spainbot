from datetime import datetime
import math
import tabula


class SpainCovid19MinistryReport:

    PDF_URL_FORMAT = "https://www.mscbs.gob.es/en/profesionales/saludPublica/ccayes/alertasActual/nCov-China/" \
                     "documentos/Actualizacion_{0}_COVID-19.pdf"

    def __init__(self, date, page, area=None):
        self._date = date
        self._page = page
        self._area = area
        self._data_frame = None

    @property
    def data_frame(self):
        if self._data_frame is None:
            data_frames = tabula.read_pdf(self.PDF_URL_FORMAT.format(self.get_pdf_id_for_date(self._date)),
                                          pages=str(self._page), area=self._area)
            self._data_frame = list(filter(lambda x: len(x) >= 22, data_frames))[0]

            for column in self._data_frame:
                self._data_frame[column.replace('*', '').strip()] = self._data_frame.pop(column)

        return self._data_frame

    @staticmethod
    def get_pdf_id_for_date(date):
        # 14/5/2020 -> id: 105
        # Weekends starting on 4/7/2020 no reports are published
        reference_date = datetime(2020, 5, 14)
        initial_weekend_without_report = datetime(2020, 7, 4)
        weekends = math.ceil((date - initial_weekend_without_report).days / 7) \
            if date > initial_weekend_without_report else 0
        return 105 + (date - reference_date).days - weekends * 2

    def get_column_data(self, column):
        ccaas_column = self.data_frame['Unnamed: 0'].astype(str)
        first_ccaa_position = ccaas_column.loc[ccaas_column.str.startswith('Andalucía', na=False)].index[0]

        cases = {}
        for i in range(first_ccaa_position, first_ccaa_position + 19):
            ccaa = self.data_frame['Unnamed: 0'][i].replace('*', '')
            value = self.data_frame[self.data_frame.columns[column]][i].split(' ')[0].replace('.', '').replace('-', '0')

            cases[ccaa] = int(value)

        return cases
