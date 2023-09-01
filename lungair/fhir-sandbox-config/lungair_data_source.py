import pandas as pd
import numpy as np
import datetime
from data_sources.patient_data_source import PatientDataSource, Patient, Observation

class LungairPatient(Patient):

  def __init__(self, patient_info):
    self.patient_info = patient_info
    self.dob = datetime.datetime(
        year = np.random.choice(np.arange(2010,2012)),
        month = np.random.choice(np.arange(1,13)),
        day = np.random.choice(np.arange(1,28)),
    )

  def get_identifier_value(self):
    return str(self.patient_info.loc['ID'])

  def get_identifier_system(self) -> str:
    return "ID column from original data excel spreadsheet"

  def get_dob(self) -> str:
    return self.dob.strftime("%Y-%m-%d")

class LungairObservation(Observation):

  def __init__(self, row_number, date, observation_type, observation_value):
    """ Create an observation based on an excel spreadsheet from the LungAIR research collaboration.

    Args:
      row_number: The row number from the spreadsheet that this observation came from
      date: The date to associate to this observation. This might have to be faked to some extent.
      observation_type: One of the types available as key values in observation_types.json
      observation_value: The value taken on by the observation
    """
    self.row_number = row_number
    self.date = date
    self.observation_type = observation_type
    self.observation_value = observation_value

  def get_identifier_value(self):
    return str(self.row_number)

  def get_identifier_system(self):
    return 'Row number in the excel spreadsheet that was used to generate this Observation'

  def get_observation_type(self):
    return self.observation_type

  def get_value(self):
    return self.observation_value

  def get_time(self):
    return self.date.strftime("%Y-%m-%d")

class LungairDataSource(PatientDataSource):

  def __init__(self, data_file_path):
    df = pd.read_excel(
      data_file_path,
      dtype = {
        'ID':str
      }
    )
    df.index += 2 # match index with row numbers shown in excel
    self.df = df

  def get_all_patients(self):
    unique_patients = self.df.drop_duplicates('ID')
    return (LungairPatient(row) for _, row in unique_patients.iterrows())

  def get_patient_observations(self, patient:LungairPatient):
    patient_id = patient.get_identifier_value()
    observations_for_patient_df = self.df[self.df['ID']==patient_id]
    observations = []
    for row_number, row in observations_for_patient_df.iterrows():
      date = patient.dob + datetime.timedelta(days=int(row['DOL']))

      for observation_type, column_name in [
        ('FIO2', 'Supplemental O2 (FiO2)'), # fraction inspired oxygen
        ('HR', 'HR (bpm)'), # heart rate
        ('PIP', 'PIP (CmH2O)'), # positive inspiratory pressure
        ('PEEP', 'PEEP (CmH2O)'), # positive end expiratory pressure
        ('SAO2', 'SPO2 (%)'), # blood oxygen saturation
        ('RR', 'RR (bpm)'), # respiratory rate
      ]:
        value_raw = str(row[column_name]).strip()
        value_is_missing = value_raw in ['*', '']
        if value_is_missing: continue
        value = float(value_raw)

        if column_name=='Supplemental O2 (FiO2)': value *= 100 # the FiO2 values in our table are fractions out of 1

        observations.append(
          LungairObservation(
            row_number = row_number,
            date = date,
            observation_type = observation_type,
            observation_value = value,
          )
        )

    return observations