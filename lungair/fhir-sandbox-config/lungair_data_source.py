import pandas as pd
import numpy as np
import datetime
import sys
import scipy.stats
import json
from pathlib import Path
from data_sources.patient_data_source import PatientDataSource, Patient, Observation

# ===========================================
# === SyntheticTableGenerator definitions ===
# ===========================================

class DolGenerator:
    """ Generator for the time range (range of "days of life" values, aka DOL values) for a synthetic time series
    of data from the LungAIR research group. Uses a log-normal distribution for number of days, and an exponential
    distribution for the starting day.
    """
    def __init__(self, log_counts_mean, log_counts_std, start_mean):
        """
        Args:
            log_counts_mean: the mean of the logarithms of the number of time points (days) in the time series.
            log_counts_std: the standard deviation of the logarithms of the number of time points (days) in the time series.
            start_mean: the mean offset (starting day) for the time series.
        """
        self.start_dist = scipy.stats.expon(scale = start_mean)
        self.log_counts_dist = scipy.stats.norm(loc = log_counts_mean, scale = log_counts_std)

    def gen(self):
        """ Generate and return a pair (starting DOL, number of DOLs). """
        dol_start = int(np.round(self.start_dist.rvs()))
        dol_count = int(np.round(np.exp(self.log_counts_dist.rvs())))
        dol_count = np.clip(dol_count, 2, 250)
        return dol_start, dol_count

class RegularTimeSeriesGenerator:
    """ Synthetic generator for time series data based on data from the LungAIR research group.
    This type of generator is suitable for a signal that has some kind of regularity, such as breathing or heart rate.
    Do not use for any kind of analysis. This is only to support demos of software interface functionality.
    """
    def __init__(self, x_hat_mu, x_hat_sigma, minmax_mu, minmax_sigma, clip = None):
        """ Initialize *feature vector* and *value range* generators.
        A feature vector is a real vector consisting of the the real part of the DFT of a time series concatenated with
        the imaginary part of the DFT. Let N denote the dimensionality of the vector, i.e. the number of features.
        A value range is described by a desired min value and max value.
        Args:
            x_hat_mu: feature vector mean, an array of length N
            x_hat_sigma: feature vector covariance matrix, an array of shape (N,N)
            minmax_mu: mean of value range (min,max), as an array of length 2
            minmax_sigma: covariance matrix of value range (min,max), an array of shape (2,2)
            clip: (optional) a pair of numbers specifying a hard range to restrict values to, which (min,max) will be clipped to
        """
        self.x_hat_dist = scipy.stats.multivariate_normal(mean=x_hat_mu, cov=x_hat_sigma, allow_singular=True)
        self.minmax_dist = scipy.stats.multivariate_normal(mean=minmax_mu, cov=minmax_sigma, allow_singular=True)
        self.clip = clip

    def gen(self, num_days):
        """ Generate and return a time series as a numpy array of length num_days."""
        x_hat_random_split = self.x_hat_dist.rvs()
        K = len(x_hat_random_split) // 2
        x_hat_random = x_hat_random_split[:K] + 1j * x_hat_random_split[K:]
        x_random = np.fft.irfft(x_hat_random, n = num_days).real

        min_val, max_val = self.minmax_dist.rvs()
        min_val  = max(0, min_val)
        max_val  = max(min_val, max_val)
        if self.clip is not None:
            min_val = np.clip(min_val, *(self.clip))
            max_val = np.clip(max_val, *(self.clip))
        x_min, x_max = x_random.min(), x_random.max()
        if np.abs(x_min-x_max) > 1e-5:
            x_random = min_val + (x_random - x_min) * (max_val - min_val) / (x_max - x_min)
        else:
            x_random[:] = (max_val + min_val) / 2
        return x_random

class PeaksTimeSeriesGenerator:
    """ Synthetic generator for time series data based on data from the LungAIR research group.
    This type of generator is suitable for an irregular signal that has a baseline value with a few peaks here and there.
    Do not use for any kind of analysis. This is only to support demos of software interface functionality.
    """
    def __init__(
        self,
        clip=(0,1),
        baseline = 0,
        negative_peaks = False,
        height_mean = 0.01,
        fwhm_mean = 1.5,
        earlier_peaks = False,
        num_peaks_mean = 10,
        cut_probability = 0.1,
        prevent_stacking = False,
    ):
        """ Initialize generator.

        Args:
            clip: the range of values for the time series, as a pair of numbers (min, max)
            baseline: the baseline signal value, which will be taken anywhere that isn't a peak
            negative_peaks: if true then peaks are subtracted from baseline rather than being added
            height_mean: the mean peak height
            fwhm_mean: the mean peak FWHM
            earlier_peaks: whether to make it more likely for peaks to show up earlier rather than later in the time series
            num_peaks_mean: the mean number of peaks
            cut_probability: the probability for a peak to gett cut and have a flat top
            prevent_stacking: whether to try and keep peaks apart
        """
        self.num_peaks_dist = scipy.stats.expon(scale=num_peaks_mean)
        self.baseline = float(baseline)
        self.clip = clip
        self.max_height = clip[1]-baseline if not negative_peaks else baseline-clip[0] # max peak height
        self.prevent_stacking = prevent_stacking
        self.fwhm_mean = fwhm_mean
        self.fwhm_dist = scipy.stats.expon(loc=1, scale=fwhm_mean-1)
        self.cut_probability = cut_probability
        self.negative_peaks = negative_peaks
        self.height_mean = height_mean
        self.earlier_peaks = earlier_peaks

    def gen(self, t):
        """ Generate and return a time series as a numpy array of the same length as t.
        Args:
            t: the array of input time points, which we generally assume to be consecutive.
        """

        dol_count = len(t)
        dol_start = t[0]
        offset_dist = scipy.stats.expon(scale=dol_count//6) if self.earlier_peaks else scipy.stats.uniform(loc=dol_start, scale=dol_count)

        num_peaks = (self.num_peaks_dist.rvs()).astype(int)

        x = self.baseline * np.ones_like(t)
        t0s = [] # maintain list of peak centers so that we can keep peaks from stacking over each other too much

        for _ in range(num_peaks):

            height = scipy.stats.expon(scale=self.height_mean).rvs()
            height = np.clip(height,0,self.max_height)

            for _ in range(30):
                offset = offset_dist.rvs()
                offset = int(np.clip(offset,0,dol_count))
                t0 = dol_start+offset
                if not self.prevent_stacking or not t0s or np.abs(np.array(t0s)-t0).min() > 2*self.fwhm_mean : break
            t0s.append(t0)


            fwhm = self.fwhm_dist.rvs()
            cut = np.random.rand() < self.cut_probability

            sigma = fwhm / 2.355
            peak  =  height * np.exp( - (t - t0)**2 / (2 * sigma**2))
            if cut:
                flatten_zone = np.abs(t-t0) < (fwhm/2)
                peak[flatten_zone] = peak[flatten_zone.argmax()]

            if self.negative_peaks: peak = - peak

            x += peak

        x = np.clip(x, *(self.clip))
        return x


class SyntheticTableGenerator:
    """A class to help initialize and manage all the synthetic data generators and produce
    a dataframe that looks like the spreadsheets from the LungAIR research group."""

    def __init__(self):
        """Initialize data generators, loading some parameters from a file and doing other things."""
        with open((Path(__file__).parent)/'synthetic_data_generation_parameters.json') as f:
            models = json.load(f)

        self.dol_generator = DolGenerator(**(models['dol']))
        self.hr_generator = RegularTimeSeriesGenerator(**(models['HR (bpm)']))
        self.rr_generator = RegularTimeSeriesGenerator(**(models['RR (bpm)']))

        self.fio2_generator = PeaksTimeSeriesGenerator(
            clip=(0,1),
            baseline = 0.21,
            negative_peaks = False,
            height_mean = 0.01,
            fwhm_mean = 1.5,
            earlier_peaks = True,
            num_peaks_mean = 10,
            cut_probability = 0.1,
            prevent_stacking = False,
        )

        self.spo2_generator = PeaksTimeSeriesGenerator(
            clip=(0,100),
            baseline = 100.,
            negative_peaks = True,
            height_mean = 4,
            fwhm_mean = 1.5,
            earlier_peaks = False,
            num_peaks_mean = 20,
            cut_probability = 0.,
            prevent_stacking = True,
        )

        self.peep_generator = PeaksTimeSeriesGenerator(
            fwhm_mean = 5,
            num_peaks_mean = 2,
            negative_peaks = False,
            earlier_peaks = False,
            cut_probability = 0.6,
            prevent_stacking = True,
            baseline = 5,
            clip=(5,7),
            height_mean = 4,
        )

        self.pip_generator = PeaksTimeSeriesGenerator(
            fwhm_mean = 2,
            num_peaks_mean = 3,
            negative_peaks = False,
            earlier_peaks = False,
            cut_probability = 0.6,
            prevent_stacking = False,
            baseline = 10,
            clip=(10,16),
            height_mean = 2,
        )

    def gen(self, id_list=None):
        """ Generate data for a number of patients/subjects using all the generators and return
        it as a pandas dataframe in the style of the LungAIR research group data spreadsheets.

        Args:
            id_list: A list of patient/subject IDs. If you don't care what they are, then just pass
                range(n) for this argument, where n is the number of patients. Or leave it as None
                to just get 50 patients.
        """

        if id_list is None:
            id_list = list(range(50))
        else:
            id_list = list(id_list)

        df_list = []
        for id in id_list:

            dol_start, dol_count = self.dol_generator.gen()
            t = np.arange(dol_start, dol_start+dol_count, 1)

            hr = self.hr_generator.gen(num_days=dol_count)
            hr = np.round(hr)


            rr = self.rr_generator.gen(num_days=dol_count)
            rr = np.round(rr)


            fio2 = self.fio2_generator.gen(t)

            spo2 = self.spo2_generator.gen(t)
            spo2 = np.round(spo2)

            # on a certain interval we will make the pip and peep be data missing, like it is in our real dataset:
            missing_start_time, missing_count = self.dol_generator.gen()
            missing_mask = (t >= missing_start_time) & (t <= missing_start_time + missing_count)

            peep = self.peep_generator.gen(t)
            peep = np.round(peep)
            peep[missing_mask] = np.nan

            pip = self.pip_generator.gen(t)
            pip = np.round(pip)
            pip[missing_mask] = np.nan

            df_list.append(
                pd.DataFrame(
                    {
                        'ID':dol_count*[id],
                        'DOL':t,
                        'HR (bpm)':hr,
                        'RR (bpm)':rr,
                        'SPO2 (%)':spo2,
                        'Supplemental O2 (FiO2)':fio2,
                        'PEEP (CmH2O)':peep,
                        'PIP (CmH2O)':pip,
                    }
                ).replace(np.nan,'*') # in our actual table * is used for missing data
            )

        return pd.concat(df_list)


# =====================================
# === LungairDataSource definitions ===
# =====================================

class LungairPatient(Patient):

  def __init__(self, patient_info, synthetic=False):
    self.patient_info = patient_info
    self.dob = datetime.datetime(
        year = np.random.choice(np.arange(2010,2012)),
        month = np.random.choice(np.arange(1,13)),
        day = np.random.choice(np.arange(1,28)),
    )

    if synthetic:
      self.identifier_system = 'ID assigned as part of synthetic data generation'
    else:
      self.identifier_system = "ID column from original data excel spreadsheet"

  def get_identifier_value(self):
    return str(self.patient_info.loc['ID'])

  def get_identifier_system(self) -> str:
    return self.identifier_system

  def get_dob(self) -> str:
    return self.dob.strftime("%Y-%m-%d")

class LungairObservation(Observation):

  def __init__(self, row_number, date, observation_type, observation_value, synthetic=False):
    """ Create an observation based on an excel spreadsheet from the LungAIR research collaboration.

    Args:
      row_number: The row number from the spreadsheet that this observation came from
      date: The date to associate to this observation. This might have to be faked to some extent.
      observation_type: One of the types available as key values in observation_types.json
      observation_value: The value taken on by the observation
      synthetic: Whether the observation is being populated with faked data.
    """
    self.row_number = row_number
    self.date = date
    self.observation_type = observation_type
    self.observation_value = observation_value

    if synthetic:
      self.identifier_system = 'Row number in synthetically generated data table'
    else:
      self.identifier_system = 'Row number in the excel spreadsheet that was used to generate this Observation'

  def get_identifier_value(self):
    return str(self.row_number)

  def get_identifier_system(self):
    return self.identifier_system

  def get_observation_type(self):
    return self.observation_type

  def get_value(self):
    return self.observation_value

  def get_time(self):
    return self.date.strftime("%Y-%m-%d")

class LungairDataSource(PatientDataSource):

  def __init__(self, data_file_path, id_list):

    self.synthetic : bool = data_file_path is None

    if not self.synthetic:
      if id_list is not None:
        print("Warning: id_list is only used with synthetic data generation, i.e. when "
              "data_file_path is null. It is ignored currently.", file=sys.stderr)
      self.df = pd.read_excel(
        data_file_path,
        dtype = {
          'ID':str
        }
      )
    else:
      table_gen = SyntheticTableGenerator()
      self.df = table_gen.gen(id_list)
      self.df['ID'] = self.df['ID'].astype(str)

    self.df.index += 2 # match index with row numbers shown in excel

  def get_all_patients(self):
    unique_patients = self.df.drop_duplicates('ID')
    return (LungairPatient(row, synthetic = self.synthetic) for _, row in unique_patients.iterrows())

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
            synthetic = self.synthetic,
          )
        )

    return observations
