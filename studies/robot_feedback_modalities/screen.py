"""Screen fixed sensor rules on all six recorded episodes and two calibrations."""
import gzip,hashlib,json,sys
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'src'))
from fyp.runtime import make_env
from monitor import SensorMonitor,PARAMETERS


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    protocol=json.loads((HERE/'monitor_protocol.json').read_text())
    for path,expected in protocol['source_hashes'].items():
        assert sha(ROOT/path)==expected,path
    assert protocol['parameters']==PARAMETERS
    trials=json.loads((ROOT/'studies/tool_hang_v1/protocol.json').read_text())['episodes']
    all_rows=[];waypoints=[];private_rows=[]
    for trial in trials+protocol['calibration_trials']:
        is_cal='folder' in trial
        folder=ROOT/trial['folder'] if is_cal else ROOT/'runs'/trial['episode_id']
        calibration=HERE/f"calibration_s0{trial['paired_state']}"/'calibration_result.json'
        c=json.loads(calibration.read_text())
        assert c['gate_pass']
        monitor=SensorMonitor(c['weights'],c['empty_quiet_opening']['1']['max_m'])
        events={e['call']:e for e in [json.loads(x) for x in (folder/'commands.jsonl').read_text().splitlines()] if e['command']['type']=='move'}
        steps=[json.loads(x) for x in (folder/'steps.jsonl').read_text().splitlines()]
        previous=[];active=None;summary=None
        for row in steps:
            identity=(row['command_id'],row['waypoint_index'])
            previous.append(row['executor_measurement'])
            if row['waypoint_index'] is None:
                continue
            if identity!=active:
                event=events[row['command_id']];wp=event['command']['waypoints'][row['waypoint_index']].copy()
                if 'quaternion_xyzw' not in wp:
                    wp['quaternion_xyzw']=row['executor_measurement']['robot0_eef_quat']
                monitor.begin(wp,previous)
                active=identity
                summary=dict(episode=folder.name,calibration=is_cal,command_id=identity[0],waypoint_index=identity[1],
                    first_step=row['step'],last_step=row['step'],requested_steps=wp['steps'],first_flags={key:None for key in monitor.counts})
                waypoints.append(summary)
            output=monitor.update(row['executor_measurement'],row['proprioception_after'])
            result=dict(episode=folder.name,calibration=is_cal,command_id=identity[0],waypoint_index=identity[1],step=row['step'],**output)
            all_rows.append(result);summary['last_step']=row['step']
            for key,value in output['flags'].items():
                if value and summary['first_flags'][key] is None:
                    summary['first_flags'][key]=row['step']
        if is_cal:
            continue
        # Geometry is private diagnostic context, not monitor input.
        config=json.loads((folder/'config.json').read_text());saved=np.load(folder/'trajectory.npz')
        env,obs,initial=make_env(**{k:config[k] for k in ['task','suite','seed','state_index','size']})
        assert np.array_equal(initial,saved['initial'])
        sim=env.sim;gripper=env.robots[0].gripper
        pads={side:set(gripper.important_geoms[side+'_fingerpad']) for side in ['left','right']}
        gripgeoms=set(gripper.contact_geoms)
        for index,state in enumerate(saved['states']):
            sim.set_state_from_flattened(state);sim.forward()
            contacts=[];pad_objects={side:set() for side in pads}
            for contact in sim.data.contact[:sim.data.ncon]:
                a,b=sim.model.geom_id2name(contact.geom1),sim.model.geom_id2name(contact.geom2)
                if a is None or b is None:
                    continue
                arobot=a.startswith(('robot0_','gripper0_','mount0_'));brobot=b.startswith(('robot0_','gripper0_','mount0_'))
                if arobot==brobot:
                    continue
                robot,other=(a,b) if arobot else (b,a)
                contacts.append(dict(robot_geom=robot,other_geom=other,gripper=robot in gripgeoms,distance_m=float(contact.dist)))
                for side,geoms in pads.items():
                    if robot in geoms:
                        for prefix in ['frame','tool','stand']:
                            if other.startswith(prefix):
                                pad_objects[side].add(prefix)
            private_rows.append(dict(episode=folder.name,step=index+1,contacts=contacts,
                both_pad_objects=sorted(pad_objects['left']&pad_objects['right']),
                geometry_only=True,native_goal_predicates=steps[index]['diagnostic_goal_predicates']))
        env.close();print(folder.name,'complete',flush=True)
    for name,rows in [('monitor_samples.jsonl.gz',all_rows),('private_contact_context.jsonl.gz',private_rows)]:
        with gzip.open(HERE/name,'wt') as f:
            for r in rows:
                f.write(json.dumps(r)+'\n')
    result=dict(scope='Development on observed traces; sensor warnings are not task/contact certificates.',
        parameters=PARAMETERS,waypoints=waypoints,samples=len(all_rows),private_contact_samples=len(private_rows),actual_astra_requests=0,
        by_scope={scope:{key:dict(flagged_waypoints=sum(w['first_flags'][key] is not None for w in waypoints if w['calibration']==cal),
            total_waypoints=sum(w['calibration']==cal for w in waypoints)) for key in ['load_change','stalled_motion','empty_sized_closure']}
            for scope,cal in [('task_traces',False),('free_verification',True)]})
    (HERE/'monitor_result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result['by_scope'],indent=2))


if __name__=='__main__':
    main()
