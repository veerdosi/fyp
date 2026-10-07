"""Paired fixed positive/negative fixtures for empty-closure stop and handoff."""
import copy,hashlib,json,sys
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'src'))
from fyp.grip_guard import GripFeedbackEpisode

protocol=json.loads((HERE/'guard_verification_protocol.json').read_text())
for path,expected in protocol['source_hashes'].items():
    assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==expected,path
calibration=protocol['calibration']
results=[]
for fixture in protocol['fixtures']:
    source=ROOT/'runs'/fixture['source_episode']
    config=json.loads((source/'config.json').read_text());saved=np.load(source/'trajectory.npz')
    events={e['call']:e for e in [json.loads(x) for x in (source/'commands.jsonl').read_text().splitlines()]}
    for interrupt in [False,True]:
        name=fixture['name']+('_guard' if interrupt else '_shadow');folder=HERE/name
        episode=GripFeedbackEpisode(folder,task=config['task'],suite=config['suite'],seed=config['seed'],state_index=config['state_index'],
            condition='fixed_sequence',size=config['size'],max_steps=600,max_calls=10,settle_steps=20,
            calibration=calibration,interrupt_empty=interrupt)
        assert np.array_equal(episode.initial,saved['initial'])
        reports=[]
        for call in fixture['source_commands']:
            command=copy.deepcopy(events[call]['command'])
            for index,wp in enumerate(command['waypoints']):
                wp['abort_if_empty_close']=call==fixture['armed_command'] and index in fixture['armed_waypoints']
            result=episode.command(dict(command=command,verification_source_call=call))
            assert 'validation_error' not in result,result
            reports.append(result['execution_report'])
        private_frame_grasp=bool(episode.env.env._check_grasp(episode.env.robots[0].gripper,episode.env.env.frame.contact_geoms))
        episode.finish('fixed_guard_verification');episode.events.close()
        recorded=np.load(folder/'trajectory.npz')
        prefix_actions_exact=np.array_equal(recorded['actions'],saved['actions'][:len(recorded['actions'])])
        prefix_states_exact=np.array_equal(recorded['states'],saved['states'][:len(recorded['states'])])
        assert prefix_actions_exact and prefix_states_exact
        expected_steps=fixture['expected_guard_steps'] if interrupt else fixture['expected_shadow_steps']
        expected_stop='armed_empty_sized_closure' if interrupt and fixture['name']=='negative' else 'sequence_complete'
        assert len(recorded['actions'])==expected_steps
        assert reports[-1]['stop_reason']==expected_stop
        if fixture['name']=='positive':
            assert private_frame_grasp
        entry=dict(fixture=fixture['name'],interrupt_empty=interrupt,folder=str(folder),source_episode=fixture['source_episode'],
            commands=fixture['source_commands'],control_steps=len(recorded['actions']),stop_reason=reports[-1]['stop_reason'],
            prefix_actions_exact=prefix_actions_exact,prefix_states_exact=prefix_states_exact,
            private_frame_grasp=private_frame_grasp,source_hashes=protocol['source_hashes'],actual_astra_requests=0,
            outcome_scope='Fixture behavior only; no complete ToolHang success claim.',all_fixture_assertions_pass=True)
        (folder/'fixture_verification.json').write_text(json.dumps(entry,indent=2)+'\n');results.append(entry)
        print(name,'passed',len(recorded['actions']),reports[-1]['stop_reason'],flush=True)
(HERE/'guard_verification_result.json').write_text(json.dumps(dict(all_pass=True,fixtures=results,actual_astra_requests=0),indent=2)+'\n')
