import os
from hypothesis import settings, Verbosity

settings.register_profile("ci", settings(max_examples=10000))
settings.register_profile("dev", settings(max_examples=100))
settings.register_profile("debug", settings(max_examples=10, verbosity=Verbosity.verbose))

if 'HYPOTHESIS_PROFILE' in os.environ:
    settings.load_profile(os.environ['HYPOTHESIS_PROFILE'])
