"""Fixed free-motion calibration of public robot/gripper/wrench feedback."""
import hashlib,json,sys,time
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'src'))
from fyp.episode import Episode
from fyp.runtime import make_env,add_robot_sensors,proprio


def save(path,data):
    path.write_text(json.dumps(data,indent=2)+'\n')


def features(p):
    opening=abs(p['robot0_gripper_qpos'][0])+abs(p['robot0_gripper_qpos'][1])
    return np.r_[1.,Rotation.from_quat(p['robot0_eef_quat']).inv().apply([0,0,-9.81]),opening]


class CalibrationEpisode(Episode):
    def __init__(self,*args,**kwargs):
        self.private_contact_rows=[]
        super().__init__(*args,**kwargs)

    def step(self,*args,**kwargs):
        super().step(*args,**kwargs)
        # Private scoring only; no controller decision reads these pairs.
        sim=self.env.sim
        gripper=set(self.env.robots[0].gripper.contact_geoms)
        pairs=[]
        for c in sim.data.contact[:sim.data.ncon]:
            a,b=sim.model.geom_id2name(c.geom1),sim.model.geom_id2name(c.geom2)
            if ((a in gripper) != (b in gripper)) and c.dist<=0:
                pairs.append([a,b])
        self.private_contact_rows.append(dict(step=self.steps,gripper_external_contact_pairs=pairs))


def run_calibration(trial,protocol):
    folder=HERE/trial['id']
    episode=CalibrationEpisode(folder,task='ToolHang',suite='robosuite',seed=trial['seed'],state_index=trial['state_index'],
        condition='fixed_sequence',size=256,max_steps=1680,max_calls=40,settle_steps=20)
    initial_q=Rotation.from_quat(episode.obs['robot0_eef_quat'])
    segments=[]
    def execute(rotation,grip,steps,label,training=False):
        q=(Rotation.from_rotvec(rotation)*initial_q).as_quat().tolist()
        first=episode.steps+1
        result=episode.command(dict(command=dict(type='move',waypoints=[dict(position=[-.10,0,1.28],
            quaternion_xyzw=q,gripper=grip,steps=steps)])))
        assert 'validation_error' not in result,result
        segments.append(dict(label=label,training=training,first_step=first,last_step=episode.steps,
            rotation_vector=rotation,gripper=grip,quiet_first_step=episode.steps-9))
    execute([0,0,0],-1,100,'approach')
    train=protocol['training_rotations'];validate=protocol['validation_rotations']
    for grip in [-1,1]:
        for index,rotation in enumerate(train):
            execute(rotation,grip,60,f'train_{grip}_{index}',training=True)
        for index,rotation in enumerate(validate):
            execute(rotation,grip,60,f'validate_{grip}_{index}')
    episode.finish('fixed_calibration_complete')
    episode.events.close()
    save(folder/'fixed_verification.json',dict(scope='Sensor calibration only; fixed Sol sequence, not a policy or manipulation-success trial.',
        actual_astra_requests=0,protocol_source_hashes=protocol['source_hashes'],segments=segments,initial_quaternion_xyzw=initial_q.as_quat().tolist()))
    save(folder/'private_contact_checks.json',episode.private_contact_rows)
    print(trial['id'],'fixed sequence recorded',flush=True)
    config=json.loads((folder/'config.json').read_text());saved=np.load(folder/'trajectory.npz')
    rows=[json.loads(s) for s in (folder/'steps.jsonl').read_text().splitlines()]
    env,obs,initial=make_env(**{k:config[k] for k in ['task','suite','seed','state_index','size']})
    assert np.array_equal(initial,saved['initial'])
    max_sensor_error=0.
    for index,action in enumerate(saved['actions']):
        obs,_,_,_=env.step(action);add_robot_sensors(env,obs)
        assert np.array_equal(env.get_sim_state(),saved['states'][index])
        measured=proprio(obs)
        for k,expected in rows[index]['proprioception_after'].items():
            max_sensor_error=max(max_sensor_error,float(np.max(np.abs(np.asarray(measured[k])-expected))))
    env.close()
    assert max_sensor_error==0.
    save(folder/'replay_verification.json',dict(all_pass=True,steps=len(rows),max_state_absolute_error=0.,
        max_public_sensor_absolute_error=max_sensor_error,
        command=f'.venv/bin/python studies/robot_feedback_modalities/calibrate.py --replay-only {trial["id"]}',
        initialization='Original seeded initialization; no forced observable updates.'))
    training=[];validation=[];motion=[];quiet_checks=[]
    for segment in segments[1:]:
        for row in rows[segment['first_step']-1:segment['last_step']]:
            p=row['proprioception_after'];before=row['executor_measurement']
            values=np.r_[p['robot0_eef_force'],p['robot0_eef_torque']]
            sample=dict(step=row['step'],gripper=segment['gripper'],features=features(p).tolist(),wrench=values.tolist(),
                opening_m=abs(p['robot0_gripper_qpos'][0])+abs(p['robot0_gripper_qpos'][1]))
            motion.append(sample)
            if row['step']<segment['quiet_first_step']:
                continue
            (training if segment['training'] else validation).append(sample)
            quiet_checks.append(dict(step=row['step'],
                linear_speed_m_s=float(np.linalg.norm(np.asarray(p['robot0_eef_pos'])-before['robot0_eef_pos'])*20),
                angular_speed_rad_s=float((Rotation.from_quat(p['robot0_eef_quat'])*Rotation.from_quat(before['robot0_eef_quat']).inv()).magnitude()*20),
                finger_speed_m_s=float(np.linalg.norm(p['robot0_gripper_qvel'])),
                private_gripper_contact_pairs=episode.private_contact_rows[row['step']-1]['gripper_external_contact_pairs']))
    x=np.asarray([r['features'] for r in training]);y=np.asarray([r['wrench'] for r in training])
    weights,_,rank,singular=np.linalg.lstsq(x,y,rcond=None)
    residual=np.asarray([r['wrench'] for r in validation])-np.asarray([r['features'] for r in validation])@weights
    force=np.linalg.norm(residual[:,:3],axis=1);torque=np.linalg.norm(residual[:,3:],axis=1)
    quiet_pass=all(r['linear_speed_m_s']<=.005 and r['angular_speed_rad_s']<=.05 and r['finger_speed_m_s']<=.001 and not r['private_gripper_contact_pairs'] for r in quiet_checks)
    fp95,tp95=float(np.percentile(force,95)),float(np.percentile(torque,95))
    summary=dict(trial=trial,training_samples=len(training),validation_samples=len(validation),rank=int(rank),
        singular_values=singular.tolist(),weights=weights.tolist(),force_validation_p95_N=fp95,torque_validation_p95_Nm=tp95,
        quiet_windows_pass=quiet_pass,gate_pass=bool(rank==5 and quiet_pass and fp95<=1 and tp95<=.05),
        validation_by_gripper={str(grip):dict(force_p95_N=float(np.percentile(force[[r['gripper']==grip for r in validation]],95)),
            torque_p95_Nm=float(np.percentile(torque[[r['gripper']==grip for r in validation]],95))) for grip in [-1,1]},
        quiet_window_checks=quiet_checks,empty_quiet_opening={str(grip):dict(min_m=min(r['opening_m'] for r in training if r['gripper']==grip),
            max_m=max(r['opening_m'] for r in training if r['gripper']==grip)) for grip in [-1,1]})
    for row in motion:
        residual=np.asarray(row['wrench'])-np.asarray(row['features'])@weights
        row['force_residual_N']=float(np.linalg.norm(residual[:3]));row['torque_residual_Nm']=float(np.linalg.norm(residual[3:]))
    save(folder/'compensated_motion.json',motion)
    save(folder/'calibration_result.json',summary)
    return summary


def main():
    protocol=json.loads((HERE/'protocol.json').read_text())
    for path,expected in protocol['source_hashes'].items():
        assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==expected,path
    results=[]
    for trial in protocol['trials']:
        results.append(run_calibration(trial,protocol))
        save(HERE/'progress.json',dict(completed_trials=len(results),results=[{k:r[k] for k in ['trial','force_validation_p95_N','torque_validation_p95_Nm','quiet_windows_pass','gate_pass']} for r in results]))
    save(HERE/'result.json',dict(scope='Observed-state sensor verification, no task-benefit or policy evidence.',protocol=protocol,
        all_calibration_gates_pass=all(r['gate_pass'] for r in results),actual_astra_requests=0,results=results))
    print(json.dumps(json.loads((HERE/'progress.json').read_text()),indent=2),flush=True)


if __name__=='__main__':
    main()
