from precise.skatertools.syntheticdata.factor import create_band_dataset
import numpy as np

# Generate random covariance matrices


def random_band_cov(n=250, n_dim=20, n_bands=5):
    xs = create_band_dataset(n=250, n_dim=20, n_bands=5)
    return np.cov(xs)