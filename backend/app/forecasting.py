"""Version 1 boundary: deliberately no probability generation or model deserialization."""
from typing import Literal
from pydantic import BaseModel

class ForecastResponseV1(BaseModel):
    api_version: Literal['v1'] = 'v1'
    target: Literal['episode_onset_next_24h'] = 'episode_onset_next_24h'
    horizon_hours: Literal[24] = 24
    status: Literal['insufficient_data','model_unavailable']
    probability: None = None
    model_version: None = None
    clinically_validated: Literal[False] = False
    emergency_actions_affected: Literal[False] = False
    reasons: list[str]
    message: str

class ForecastServiceV1:
    def status(self,*,data_ready=False):
        # This argument is an internal future data-review boundary, NOT an HTTP toggle.
        # Offline experiment success never changes it or publishes an artifact.
        if data_ready:
            return ForecastResponseV1(status='model_unavailable',reasons=['no_validated_model'],message='No validated forecasting model is available. Research experiments do not enable predictions.')
        return ForecastResponseV1(status='insufficient_data',reasons=[
            'no_verified_longitudinal_provenance','no_explicit_observation_coverage',
            'no_verified_point_in_time_history','no_validated_model'],
            message='Forecasting is in development. Verified longitudinal observations and a validated model are not available. No risk score is generated.')
