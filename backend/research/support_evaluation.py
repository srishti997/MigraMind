"""Offline descriptive usability metrics; no auto-tracking or inferred call completion."""
from typing import Literal
from pydantic import BaseModel, Field, ConfigDict, model_validator
from app.support_engine import ACTIONS
class Trial(BaseModel):
    model_config=ConfigDict(extra='forbid')
    source: Literal['simulated_test','real_user_study']
    policy: Literal['fixed','adaptive']
    completed: bool|None=Field(default=None,strict=True)
    interactions: int|None=Field(default=None,ge=0,strict=True)
    chosen_action: str|None=None
    explicit_first_choice: str|None=None
    order_before: list[str]=Field(default_factory=list)
    order_after: list[str]=Field(default_factory=list)
    @model_validator(mode='after')
    def actions(self):
        for action in [self.chosen_action,self.explicit_first_choice,*self.order_before,*self.order_after]:
            if action is not None and action not in ACTIONS:raise ValueError('Nonemergency support action required')
        for order in [self.order_before,self.order_after]:
            if len(order)!=len(set(order)):raise ValueError('Order must not repeat actions')
        return self

def evaluate_trials(trials):
    validated=[t if isinstance(t,Trial) else Trial.model_validate(t) for t in trials]
    groups={}
    for source in ['simulated_test','real_user_study']:
        groups[source]={}
        for policy in ['fixed','adaptive']:
            rows=[t for t in validated if t.source==source and t.policy==policy]
            completion=[t.completed for t in rows if t.completed is not None]
            interactions=[t.interactions for t in rows if t.interactions is not None]
            alignment=[t.chosen_action==t.explicit_first_choice for t in rows if t.chosen_action and t.explicit_first_choice]
            changes=[t.order_before[0]!=t.order_after[0] for t in rows if t.order_before and t.order_after]
            mean=lambda values:sum(values)/len(values) if values else None
            groups[source][policy]={'trials':len(rows),'completion_rate':mean(completion),'completion_observations':len(completion),
                'mean_interactions':mean(interactions),'interaction_observations':len(interactions),
                'preference_alignment':mean(alignment),'alignment_observations':len(alignment),
                'top_recommendation_change_rate':mean(changes),'change_observations':len(changes)}
    return {'evaluation_version':'support-usability-v1','results_by_source':groups,
        'limitations':'Descriptive usability only. Simulated tests and real outcomes are never pooled. A link click is not task completion, message delivery, or medical benefit.'}

if __name__=='__main__':
    import argparse,json
    from pathlib import Path
    parser=argparse.ArgumentParser(description='Offline support usability evaluation; no synthetic data generator')
    parser.add_argument('--input',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    try:
        data=json.loads(args.input.read_text(encoding='utf-8-sig'))
        report=evaluate_trials(data)
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(report,indent=2,allow_nan=False),encoding='utf-8')
        print('{"status":"descriptive_report_written","automatic_tracking":false}')
    except (ValueError,TypeError,OSError):
        print('{"status":"invalid_local_input"}');raise SystemExit(2)
